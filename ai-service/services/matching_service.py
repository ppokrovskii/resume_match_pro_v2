"""
Document matching service using vector similarity
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import re

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from models.embedding import MatchResult, MatchResponse
from utils.database import EmbeddingRepository
from utils.error_handler import MatchingError, DatabaseError
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for matching CVs with Job Descriptions using embeddings"""
    
    def __init__(self):
        self.repository = EmbeddingRepository()
        self.embedding_service = EmbeddingService()
        
        # Matching configuration
        self.similarity_threshold = 0.6  # Minimum similarity for a match
        self.skill_keywords = self._load_skill_keywords()
    
    def _load_skill_keywords(self) -> Dict[str, List[str]]:
        """Load skill keywords for different categories"""
        return {
            'programming': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring',
                'html', 'css', 'sass', 'less'
            ],
            'databases': [
                'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
                'oracle', 'sqlite', 'cassandra', 'dynamodb'
            ],
            'cloud': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'jenkins', 'gitlab', 'github actions'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'data science', 'analytics',
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
                'tableau', 'power bi', 'r'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'project management', 'agile', 'scrum', 'collaboration'
            ]
        }
    
    def _extract_skills_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract skills from text using keyword matching"""
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills in self.skill_keywords.items():
            found_skills[category] = []
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills[category].append(skill)
        
        return found_skills
    
    def _calculate_skill_overlap(self, cv_skills: Dict[str, List[str]], jd_skills: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
        """Calculate skill overlap and gaps"""
        matching_skills = []
        skill_gaps = []
        
        for category in jd_skills:
            jd_category_skills = set(skill.lower() for skill in jd_skills[category])
            cv_category_skills = set(skill.lower() for skill in cv_skills.get(category, []))
            
            # Find matching skills
            matches = jd_category_skills.intersection(cv_category_skills)
            matching_skills.extend(matches)
            
            # Find skill gaps (required but not present in CV)
            gaps = jd_category_skills - cv_category_skills
            skill_gaps.extend(gaps)
        
        return list(set(matching_skills)), list(set(skill_gaps))
    
    def _calculate_similarity_score(self, cv_embedding: List[float], jd_embedding: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            cv_vector = np.array(cv_embedding).reshape(1, -1)
            jd_vector = np.array(jd_embedding).reshape(1, -1)
            
            similarity = cosine_similarity(cv_vector, jd_vector)[0][0]
            return max(0.0, min(1.0, similarity))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_match_score(
        self, 
        similarity_score: float, 
        skill_overlap_ratio: float,
        confidence_factors: Dict[str, float]
    ) -> Tuple[int, float]:
        """
        Calculate final match score (0-100) and confidence level
        """
        # Weighted scoring
        weights = {
            'semantic_similarity': 0.6,
            'skill_overlap': 0.3,
            'text_quality': 0.1
        }
        
        # Calculate weighted score
        weighted_score = (
            similarity_score * weights['semantic_similarity'] +
            skill_overlap_ratio * weights['skill_overlap'] +
            confidence_factors.get('text_quality', 0.5) * weights['text_quality']
        )
        
        # Convert to 0-100 scale
        match_score = int(weighted_score * 100)
        
        # Calculate confidence level
        confidence_level = min(1.0, (
            confidence_factors.get('cv_completeness', 0.5) +
            confidence_factors.get('jd_clarity', 0.5) +
            (1.0 if similarity_score > 0.7 else 0.5)
        ) / 3)
        
        return match_score, confidence_level
    
    async def match_cv_with_jobs(
        self, 
        cv_id: UUID, 
        jd_ids: List[UUID], 
        user_id: UUID
    ) -> MatchResponse:
        """
        Match a CV with multiple job descriptions
        """
        try:
            start_time = time.time()
            
            # Get CV embedding
            cv_embedding_data = self.repository.get_embedding(cv_id)
            if not cv_embedding_data:
                raise MatchingError(f"No embedding found for CV {cv_id}")
            
            cv_embedding = cv_embedding_data['embedding']
            cv_text = ' '.join(cv_embedding_data['text_chunks'])
            cv_skills = self._extract_skills_from_text(cv_text)
            
            matches = []
            
            # Process each job description
            for jd_id in jd_ids:
                try:
                    # Get JD embedding
                    jd_embedding_data = self.repository.get_embedding(jd_id)
                    if not jd_embedding_data:
                        logger.warning(f"No embedding found for JD {jd_id}")
                        continue
                    
                    jd_embedding = jd_embedding_data['embedding']
                    jd_text = ' '.join(jd_embedding_data['text_chunks'])
                    jd_skills = self._extract_skills_from_text(jd_text)
                    
                    # Calculate similarity
                    similarity_score = self._calculate_similarity_score(cv_embedding, jd_embedding)
                    
                    # Calculate skill overlap
                    matching_skills, skill_gaps = self._calculate_skill_overlap(cv_skills, jd_skills)
                    
                    # Calculate skill overlap ratio
                    total_required_skills = sum(len(skills) for skills in jd_skills.values())
                    skill_overlap_ratio = len(matching_skills) / max(1, total_required_skills)
                    
                    # Calculate confidence factors
                    confidence_factors = {
                        'cv_completeness': min(1.0, len(cv_text) / 1000),  # Based on text length
                        'jd_clarity': min(1.0, len(jd_text) / 500),
                        'text_quality': 0.8  # Could be enhanced with NLP analysis
                    }
                    
                    # Calculate final match score
                    match_score, confidence_level = self._calculate_match_score(
                        similarity_score, skill_overlap_ratio, confidence_factors
                    )
                    
                    # Only include matches above threshold
                    if similarity_score >= self.similarity_threshold:
                        match_result = MatchResult(
                            cv_id=cv_id,
                            jd_id=jd_id,
                            similarity_score=similarity_score,
                            match_score=match_score,
                            matching_keywords=matching_skills[:10],  # Top 10
                            skill_gaps=skill_gaps[:10],  # Top 10 gaps
                            confidence_level=confidence_level
                        )
                        matches.append(match_result)
                        
                        logger.debug(f"Match created: CV {cv_id} -> JD {jd_id}, Score: {match_score}")
                
                except Exception as e:
                    logger.error(f"Failed to process JD {jd_id}: {e}")
                    continue
            
            # Sort matches by score (descending)
            matches.sort(key=lambda x: x.match_score, reverse=True)
            
            # Save match results to database
            try:
                match_data = []
                for match in matches:
                    match_data.append({
                        'cv_id': match.cv_id,
                        'jd_id': match.jd_id,
                        'user_id': user_id,
                        'match_score': match.match_score,
                        'similarity_breakdown': {
                            'similarity_score': match.similarity_score,
                            'confidence_level': match.confidence_level
                        },
                        'matching_skills': match.matching_keywords,
                        'skill_gaps': match.skill_gaps,
                        'confidence_level': match.confidence_level
                    })
                
                self.repository.save_match_results(match_data)
                logger.info(f"Saved {len(match_data)} match results to database")
                
            except Exception as e:
                logger.warning(f"Failed to save match results: {e}")
                # Continue anyway - matching worked even if saving failed
            
            processing_time = int((time.time() - start_time) * 1000)
            
            response = MatchResponse(
                matches=matches,
                cv_id=cv_id,
                processing_time_ms=processing_time,
                total_matches=len(matches)
            )
            
            logger.info(f"Matching completed: {len(matches)} matches in {processing_time}ms")
            return response
            
        except Exception as e:
            logger.error(f"CV matching failed: {e}")
            if isinstance(e, MatchingError):
                raise
            raise MatchingError(f"Failed to match CV with jobs: {str(e)}")
    
    def get_cached_matches(self, cv_id: UUID, jd_ids: List[UUID]) -> List[Dict[str, Any]]:
        """Get existing match results from database"""
        try:
            return self.repository.get_match_results(cv_id, jd_ids)
        except Exception as e:
            logger.error(f"Failed to get cached matches: {e}")
            return []
    
    async def similarity_search(
        self, 
        query: str, 
        user_id: UUID,
        document_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search
        """
        try:
            start_time = time.time()
            
            # Generate embedding for query
            query_embedding, _ = await self.embedding_service.generate_embedding(query)
            
            # Search for similar documents
            results = self.repository.similarity_search(
                query_embedding=query_embedding,
                user_id=user_id,
                document_type=document_type,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            # Enhance results with skill analysis
            enhanced_results = []
            query_skills = self._extract_skills_from_text(query)
            
            for result in results:
                document_text = result.get('text_content', '')
                document_skills = self._extract_skills_from_text(document_text)
                
                matching_skills, _ = self._calculate_skill_overlap(document_skills, query_skills)
                
                enhanced_result = {
                    **result,
                    'matching_skills': matching_skills[:5],  # Top 5 matching skills
                    'processing_time_ms': int((time.time() - start_time) * 1000)
                }
                enhanced_results.append(enhanced_result)
            
            logger.info(f"Similarity search completed: {len(results)} results")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise MatchingError(f"Similarity search failed: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for matching service"""
        try:
            # Check database connection
            db_healthy = True
            try:
                self.repository.get_embedding_stats()
            except Exception:
                db_healthy = False
            
            # Check embedding service
            embedding_healthy = True
            try:
                embedding_health = self.embedding_service.health_check()
                embedding_healthy = embedding_health['status'] == 'healthy'
            except Exception:
                embedding_healthy = False
            
            overall_healthy = db_healthy and embedding_healthy
            
            return {
                'status': 'healthy' if overall_healthy else 'unhealthy',
                'database': 'healthy' if db_healthy else 'unhealthy',
                'embedding_service': 'healthy' if embedding_healthy else 'unhealthy',
                'similarity_threshold': self.similarity_threshold
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }





