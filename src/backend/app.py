import logging
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from sqlalchemy.orm import defer
from config import Config
from db import init_db, get_db_session
from models import QRCode
from qr_service import generate_qr_png_bytes, generate_qr_base64

# Configure structured logging for backend API
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory initializing Flask REST API."""
    app = Flask(__name__)
    
    # Enable CORS for communication with Vue 3 frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Automatically initialize database schema on startup
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            logger.error(f"Database initialization warning: {e}")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """
        Healthcheck endpoint verifying backend status and PostgreSQL connectivity.
        Used by Docker container healthcheck and Kubernetes liveness/readiness probes.
        """
        db_ok = False
        try:
            with get_db_session() as session:
                session.execute(QRCode.__table__.select().limit(1))
            db_ok = True
        except Exception as e:
            logger.warning(f"Healthcheck failed querying database: {e}")

        status = "healthy" if db_ok else "degraded"
        return jsonify({
            "status": status,
            "database": "connected" if db_ok else "unavailable"
        }), (200 if status == "healthy" else 503)

    @app.route("/api/qrcodes", methods=["GET"])
    def list_qrcodes():
        """
        Return list of stored QR codes ordered descending by creation date.
        Supports optional search query parameter '?search=...' (searches code_number, description, content).
        Optimized: 'image_data' column is deferred to prevent transferring heavy binary payloads.
        """
        search = request.args.get("search", "").strip()
        with get_db_session() as session:
            query = session.query(QRCode)
            if search:
                term = f"%{search}%"
                query = query.filter(
                    (QRCode.code_number.ilike(term)) |
                    (QRCode.description.ilike(term)) |
                    (QRCode.content.ilike(term))
                )
            # Defer loading binary image data for lower memory usage and faster response
            records = query.options(defer(QRCode.image_data)).order_by(QRCode.id.desc()).all()
            return jsonify([record.to_dict() for record in records])

    @app.route("/api/qrcodes/<int:qr_id>", methods=["GET"])
    def get_qrcode(qr_id):
        """Return metadata of a specific QR code by primary key ID."""
        with get_db_session() as session:
            record = session.query(QRCode).options(defer(QRCode.image_data)).filter(QRCode.id == qr_id).first()
            if not record:
                return jsonify({"error": "QR kód nenalezen"}), 404
            return jsonify(record.to_dict())

    @app.route("/api/qrcodes/<int:qr_id>/image", methods=["GET"])
    def get_qrcode_image(qr_id):
        """
        Stream raw PNG image bytes directly from database (BYTEA column).
        If '?download=1' is set, adds Content-Disposition header to prompt browser download.
        """
        with get_db_session() as session:
            record = session.query(QRCode).filter(QRCode.id == qr_id).first()
            if not record or not record.image_data:
                return jsonify({"error": "QR kód nebo obrázek nenalezen"}), 404

            image_bytes = bytes(record.image_data)
            code_number = record.code_number

        download = request.args.get("download", "0") in ("1", "true")
        headers = {
            "Cache-Control": "public, max-age=86400",  # Cache in client browser for 24 hours
        }
        if download:
            filename = f"qr_{code_number or qr_id}.png"
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        return Response(image_bytes, mimetype="image/png", headers=headers)

    @app.route("/api/qrcodes/preview", methods=["POST"])
    def preview_qrcode():
        """
        Generate on-the-fly base64 preview without saving to database.
        Used for real-time live preview in the frontend creation form.
        """
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"error": "Obsah QR kódu je povinný"}), 400

        try:
            preview_base64 = generate_qr_base64(content)
            return jsonify({"preview": preview_base64})
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return jsonify({"error": "Chyba při generování QR kódu"}), 500

    @app.route("/api/qrcodes", methods=["POST"])
    def create_qrcode():
        """
        Create a new QR code:
        1. Generates binary PNG image using qrcode/Pillow.
        2. Assigns sequential code_number (e.g. QR-0001) if not provided by user.
        3. Persists metadata and binary image into PostgreSQL within a managed session.
        """
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        description = (data.get("description") or "").strip()
        code_number = (data.get("code_number") or "").strip()

        if not content:
            return jsonify({"error": "Obsah (text) QR kódu je povinný."}), 400

        # 1. Generate PNG image bytes
        try:
            image_bytes = generate_qr_png_bytes(content)
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return jsonify({"error": "Chyba při generování QR kódu."}), 500

        with get_db_session() as session:
            # Auto-generate code_number if omitted
            if not code_number:
                count = session.query(QRCode).count()
                code_number = f"QR-{count + 1:04d}"

            # 2. Save record into relational database
            try:
                new_record = QRCode(
                    code_number=code_number,
                    description=description,
                    content=content,
                    image_data=image_bytes,
                )
                session.add(new_record)
                session.flush()  # Populate auto-generated primary key ID
                result = new_record.to_dict()
                return jsonify(result), 201
            except Exception as e:
                logger.error(f"Error saving to database: {e}")
                return jsonify({"error": f"Chyba při zápisu do databáze: {str(e)}"}), 500

    @app.route("/api/qrcodes/<int:qr_id>", methods=["DELETE"])
    def delete_qrcode_item(qr_id):
        """Delete QR code record and its associated image data from database by ID."""
        with get_db_session() as session:
            record = session.query(QRCode).filter(QRCode.id == qr_id).first()
            if not record:
                return jsonify({"error": "QR kód nenalezen"}), 404

            session.delete(record)

        return jsonify({"message": f"QR kód #{qr_id} byl úspěšně smazán."}), 200

    return app

app = create_app()

if __name__ == "__main__":
    # Direct execution for standalone local development outside WSGI container
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
