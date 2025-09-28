"""
Health check routes for AI service
"""

from flask import Blueprint, jsonify
from services.embedding_service import EmbeddingService
from services.matching_service import MatchingService

health_bp = Blueprint('health', __name__)
embedding_service = EmbeddingService()
matching_service = MatchingService()


@health_bp.route('/', methods=['GET'])
@health_bp.route('/check', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check embedding service
        embedding_health = embedding_service.health_check()
        
        # Check matching service
        matching_health = matching_service.health_check()
        
        # Overall health status
        overall_healthy = (
            embedding_health.get('status') == 'healthy' and
            matching_health.get('status') == 'healthy'
        )
        
        health_status = {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'embedding_service': embedding_health,
            'matching_service': matching_health,
            'timestamp': embedding_health.get('timestamp')
        }
        
        status_code = 200 if overall_healthy else 503
        
        return jsonify({
            'success': True,
            'data': health_status,
            'meta': {
                'service': 'ai-service',
                'version': '1.0.0'
            }
        }), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'HEALTH_CHECK_FAILED',
                'message': str(e)
            },
            'meta': {
                'service': 'ai-service',
                'version': '1.0.0'
            }
        }), 503


@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check if services are ready to handle requests
        embedding_health = embedding_service.health_check()
        matching_health = matching_service.health_check()
        
        ready = (
            embedding_health.get('status') == 'healthy' and
            matching_health.get('status') == 'healthy'
        )
        
        return jsonify({
            'success': True,
            'data': {'ready': ready},
            'meta': {
                'service': 'ai-service',
                'version': '1.0.0'
            }
        }), 200 if ready else 503
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'READINESS_CHECK_FAILED',
                'message': str(e)
            }
        }), 503


@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Liveness check endpoint"""
    return jsonify({
        'success': True,
        'data': {'alive': True},
        'meta': {
            'service': 'ai-service',
            'version': '1.0.0'
        }
    }), 200


@health_bp.route('/stats', methods=['GET'])
def service_stats():
    """Service statistics endpoint"""
    try:
        from utils.database import EmbeddingRepository
        
        repository = EmbeddingRepository()
        stats = repository.get_embedding_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'meta': {
                'service': 'ai-service',
                'endpoint': 'stats'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'STATS_ERROR',
                'message': str(e)
            }
        }), 500





