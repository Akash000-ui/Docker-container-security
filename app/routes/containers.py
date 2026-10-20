"""Container inventory and detail routes."""

from flask import Blueprint, jsonify, render_template
from flask_login import login_required

from app.services.docker_service import DockerException, DockerService, NotFound
from app.services.inventory_service import sync_inventory


containers_bp = Blueprint("containers", __name__)


def _service() -> DockerService:
    return DockerService()


@containers_bp.get("/containers")
@login_required
def list_page():
    """Render the Docker container inventory page."""

    try:
        containers = _service().list_containers()
        sync_inventory(containers)
        return render_template("containers/list.html", containers=containers, docker_error=None)
    except DockerException as error:
        return render_template("containers/list.html", containers=[], docker_error=str(error)), 503


@containers_bp.get("/containers/<docker_id>")
@login_required
def detail_page(docker_id: str):
    """Render detailed metadata for a Docker container."""

    try:
        container = _service().get_container(docker_id)
    except NotFound:
        return render_template("errors/404.html"), 404
    except DockerException as error:
        return render_template("errors/500.html", error=error), 503

    return render_template("containers/detail.html", container=container)


@containers_bp.get("/api/containers")
@login_required
def list_api():
    """Return the current Docker inventory as JSON."""

    try:
        containers = _service().list_containers()
        sync_inventory(containers)
        return jsonify({"containers": containers, "count": len(containers)})
    except DockerException as error:
        return jsonify({"error": "Docker Engine is unavailable", "detail": str(error)}), 503


@containers_bp.get("/api/containers/<docker_id>")
@login_required
def detail_api(docker_id: str):
    """Return detailed Docker metadata as JSON."""

    try:
        return jsonify(_service().get_container(docker_id))
    except NotFound:
        return jsonify({"error": "Container not found"}), 404
    except DockerException as error:
        return jsonify({"error": "Docker Engine is unavailable", "detail": str(error)}), 503

