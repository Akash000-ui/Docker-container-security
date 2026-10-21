"""Container inventory and detail routes."""

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.services.docker_service import DockerException, DockerService, NotFound
from app.services.inventory_service import record_metric, sync_inventory
from app.services.security_service import run_security_analysis


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


@containers_bp.get("/containers/<docker_id>/monitor")
@login_required
def monitor_page(docker_id: str):
    """Render live runtime monitoring for one container."""

    try:
        container = _service().get_container(docker_id)
    except NotFound:
        return render_template("errors/404.html"), 404
    except DockerException as error:
        return render_template("errors/500.html", error=error), 503

    return render_template("containers/monitor.html", container=container)


@containers_bp.get("/containers/<docker_id>/security")
@login_required
def security_page(docker_id: str):
    """Analyze a container and render its failed security checks."""

    try:
        container = _service().get_container(docker_id)
        sync_inventory([container])
        analysis = run_security_analysis(docker_id, container)
    except NotFound:
        return render_template("errors/404.html"), 404
    except (DockerException, ValueError) as error:
        return render_template("errors/500.html", error=error), 503

    return render_template(
        "containers/security.html",
        container=container,
        findings=analysis["findings"],
        analysis=analysis,
    )


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


@containers_bp.get("/api/containers/<docker_id>/security")
@login_required
def security_api(docker_id: str):
    """Analyze a container and return its security findings as JSON."""

    try:
        container = _service().get_container(docker_id)
        sync_inventory([container])
        analysis = run_security_analysis(docker_id, container)
        return jsonify(
            {
                "container_id": docker_id,
                "finding_count": len(analysis["findings"]),
                **analysis,
            }
        )
    except NotFound:
        return jsonify({"error": "Container not found"}), 404
    except (DockerException, ValueError) as error:
        return jsonify({"error": "Security analysis unavailable", "detail": str(error)}), 503


@containers_bp.get("/api/containers/<docker_id>/stats")
@login_required
def stats_api(docker_id: str):
    """Return one CPU, memory, network, and block I/O snapshot."""

    try:
        stats = _service().get_stats(docker_id)
        record_metric(stats)
        return jsonify(stats)
    except NotFound:
        return jsonify({"error": "Container not found"}), 404
    except DockerException as error:
        return jsonify({"error": "Container statistics unavailable", "detail": str(error)}), 503


@containers_bp.get("/api/containers/<docker_id>/logs")
@login_required
def logs_api(docker_id: str):
    """Return recent container logs."""

    try:
        tail = int(request.args.get("tail", 200))
    except ValueError:
        tail = 200

    try:
        return jsonify({"logs": _service().get_logs(docker_id, tail=tail), "tail": max(1, min(tail, 1000))})
    except NotFound:
        return jsonify({"error": "Container not found"}), 404
    except DockerException as error:
        return jsonify({"error": "Container logs unavailable", "detail": str(error)}), 503


@containers_bp.get("/api/containers/<docker_id>/processes")
@login_required
def processes_api(docker_id: str):
    """Return the process table reported by Docker."""

    try:
        return jsonify(_service().get_processes(docker_id))
    except NotFound:
        return jsonify({"error": "Container not found"}), 404
    except DockerException as error:
        return jsonify({"error": "Container processes unavailable", "detail": str(error)}), 503

