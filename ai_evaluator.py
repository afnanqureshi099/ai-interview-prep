"""
AI Evaluator Engine
-------------------
Provides multi-dimensional heuristic and semantic scoring for candidate responses.
Evaluates answers across 3 core pillars:
  1. Technical Accuracy (concept coverage, keyword density, terminology precision)
  2. Clarity & Communication (sentence structure, readability, flow, coherence)
  3. Completeness & Depth (coverage relative to expected seniority level, trade-offs, examples)

Returns structured scorecards, feedback breakdowns, and model comparisons.
"""

import re
import math


class AIEvaluator:

    # Stopwords list for keyword normalization
    STOPWORDS = {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are',
        'aren\'t', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both',
        'but', 'by', 'can', 'cannot', 'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t',
        'doing', 'don\'t', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn\'t',
        'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
        'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'its', 'itself', 'let\'s',
        'me', 'more', 'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once',
        'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she',
        'should', 'shouldn\'t', 'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them',
        'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under',
        'until', 'up', 'very', 'was', 'wasn\'t', 'we', 'were', 'weren\'t', 'what', 'when', 'where', 'which',
        'while', 'who', 'whom', 'why', 'with', 'won\'t', 'would', 'wouldn\'t', 'you', 'your', 'yours', 'yourself'
    }

    # Transition & structuring words that demonstrate professional communication
    STRUCTURING_WORDS = {
        'firstly', 'secondly', 'furthermore', 'moreover', 'in addition', 'consequently',
        'for example', 'for instance', 'specifically', 'in contrast', 'however', 'on the other hand',
        'therefore', 'as a result', 'in conclusion', 'to summarize', 'trade-off', 'tradeoff',
        'architecture', 'implementation', 'scalable', 'bottleneck', 'optimization'
    }

    # Expected word counts by seniority level
    WORD_TARGETS = {
        'Junior': {'min': 35, 'ideal': 85, 'max': 250},
        'Mid': {'min': 55, 'ideal': 130, 'max': 350},
        'Senior': {'min': 80, 'ideal': 180, 'max': 450}
    }

    @classmethod
    def evaluate_response(cls, user_answer: str, question_dict: dict) -> dict:
        """
        Analyzes a single user answer against a question definition.
        Returns a dictionary with scores, feedback, strengths, and improvements.
        """
        cleaned_answer = (user_answer or "").strip()
        domain = question_dict.get('domain', 'Software Engineering')
        difficulty = question_dict.get('difficulty', 'Mid')
        expected_keywords_str = question_dict.get('expected_keywords', '')
        model_answer = question_dict.get('model_answer', '')

        # Parse expected keywords
        expected_keywords = [
            k.strip().lower() for k in expected_keywords_str.split(',') if k.strip()
        ]

        # Case 1: Empty or extremely short response (< 5 words)
        words = re.findall(r'\b\w+\b', cleaned_answer)
        word_count = len(words)

        if word_count < 5:
            return {
                'technical_score': 10.0,
                'clarity_score': 20.0,
                'completeness_score': 10.0,
                'overall_score': 13.0,
                'feedback': 'The response is too brief or incomplete to assess your technical capability. In an interview, always explain your reasoning thoroughly with examples.',
                'strengths': 'Attempted the question.',
                'improvements': 'Provide an in-depth answer defining core concepts, trade-offs, and practical examples.',
                'matched_keywords': [],
                'missing_keywords': expected_keywords,
                'model_answer': model_answer,
                'rating_label': 'Needs Improvement'
            }

        # 1. Technical Accuracy Calculation (Keyword & Terminology Matching)
        lower_answer = cleaned_answer.lower()
        matched_kw = []
        missing_kw = []

        for kw in expected_keywords:
            # Check for keyword phrase in response
            kw_clean = kw.lower().strip()
            # Allow partial stem or exact word match
            pattern = r'\b' + re.escape(kw_clean) + r'\b'
            if re.search(pattern, lower_answer) or kw_clean in lower_answer:
                matched_kw.append(kw)
            else:
                missing_kw.append(kw)

        total_kw = max(len(expected_keywords), 1)
        kw_ratio = len(matched_kw) / total_kw

        # Technical score calculation: base score from keyword coverage + vocabulary relevance
        technical_score = min(100.0, max(25.0, (kw_ratio * 70.0) + 20.0 + min(word_count * 0.1, 10.0)))

        # 2. Clarity & Communication Calculation
        # Evaluates sentence count, average sentence length, structuring terms
        sentences = [s.strip() for s in re.split(r'[.!?]+', cleaned_answer) if len(s.strip()) > 3]
        num_sentences = max(len(sentences), 1)
        avg_sentence_len = word_count / num_sentences

        clarity_score = 70.0  # baseline solid score

        # Reward healthy sentence lengths (12 to 25 words per sentence)
        if 10 <= avg_sentence_len <= 28:
            clarity_score += 15.0
        elif avg_sentence_len < 8 or avg_sentence_len > 35:
            clarity_score -= 15.0

        # Reward use of structuring transition terms
        structure_count = sum(1 for term in cls.STRUCTURING_WORDS if term in lower_answer)
        clarity_score += min(structure_count * 5.0, 15.0)

        # Cap clarity between 30 and 100
        clarity_score = min(100.0, max(30.0, clarity_score))

        # 3. Completeness & Depth Calculation
        targets = cls.WORD_TARGETS.get(difficulty, cls.WORD_TARGETS['Mid'])
        if word_count < targets['min']:
            completeness_score = (word_count / targets['min']) * 60.0
        elif word_count <= targets['ideal']:
            completeness_score = 60.0 + ((word_count - targets['min']) / (targets['ideal'] - targets['min'])) * 35.0
        else:
            # Good depth, minor penalty only if excessively rambling (> max)
            completeness_score = 95.0
            if word_count > targets['max']:
                completeness_score = max(75.0, 95.0 - (word_count - targets['max']) * 0.05)

        # Completeness also incorporates how many of the core concepts were addressed
        completeness_score = (completeness_score * 0.6) + (kw_ratio * 100.0 * 0.4)
        completeness_score = min(100.0, max(20.0, completeness_score))

        # 4. Overall Weighted Score
        # Technical Accuracy (45%), Completeness (30%), Clarity (25%)
        overall_score = round(
            (technical_score * 0.45) + (completeness_score * 0.30) + (clarity_score * 0.25), 1
        )
        technical_score = round(technical_score, 1)
        clarity_score = round(clarity_score, 1)
        completeness_score = round(completeness_score, 1)

        # Rating label
        if overall_score >= 88:
            rating_label = 'Exceptional'
        elif overall_score >= 75:
            rating_label = 'Strong Hire'
        elif overall_score >= 60:
            rating_label = 'Competent / Developing'
        else:
            rating_label = 'Needs Improvement'

        # Generate specific, constructive feedback
        strengths_list = []
        improvements_list = []

        # Strengths
        if matched_kw:
            strengths_list.append(f"Successfully incorporated key domain concepts: {', '.join(matched_kw[:4])}.")
        if word_count >= targets['min']:
            strengths_list.append(f"Provided good elaboration ({word_count} words) appropriate for a {difficulty}-level role.")
        if structure_count > 0:
            strengths_list.append("Effective communication with logical flow and transition phrases.")
        if not strengths_list:
            strengths_list.append("Conveyed initial thoughts on the topic.")

        # Improvements
        if missing_kw:
            improvements_list.append(f"Consider exploring missing core concepts such as: {', '.join(missing_kw[:3])}.")
        if word_count < targets['min']:
            improvements_list.append(f"Answer was relatively concise. Aim for at least {targets['min']} words to substantiate your points.")
        if avg_sentence_len > 30:
            improvements_list.append("Sentences are quite long; consider breaking complex thoughts into punchier, bulleted points.")
        if domain == 'HR/Behavioral' and not any(k in lower_answer for k in ['situation', 'task', 'action', 'result', 'learned', 'outcome']):
            improvements_list.append("Structure behavioral answers using the STAR method (Situation, Task, Action, Result).")
        if not improvements_list:
            improvements_list.append("Outstanding response. Maintain this clarity and depth in live technical panel interviews.")

        # General summary feedback
        if overall_score >= 85:
            summary_feedback = f"Excellent response! You clearly understand {domain} fundamentals and articulated your thought process with high technical rigor."
        elif overall_score >= 70:
            summary_feedback = f"Solid answer. You demonstrated good grasp of the subject matter, but touching upon deeper trade-offs and edge cases would elevate it further."
        elif overall_score >= 50:
            summary_feedback = "Acceptable foundation, but the explanation lacks depth in technical terminology and real-world system considerations."
        else:
            summary_feedback = "The answer missed key technical points. Review the model answer below and focus on explaining core architectural mechanisms."

        return {
            'technical_score': technical_score,
            'clarity_score': clarity_score,
            'completeness_score': completeness_score,
            'overall_score': overall_score,
            'feedback': summary_feedback,
            'strengths': " ".join(strengths_list),
            'improvements': " ".join(improvements_list),
            'matched_keywords': matched_kw,
            'missing_keywords': missing_kw,
            'model_answer': model_answer,
            'rating_label': rating_label
        }
