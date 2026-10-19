/**
 * Live Interactive Mock Interview Runtime
 * Handles: Question navigation, countdown timer, Web Speech API speech-to-text,
 * async AI evaluation submissions, real-time score meter rendering, and final report transition.
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!window.INTERVIEW_CONFIG) return;
    initInterviewEngine();
});

function initInterviewEngine() {
    const config = window.INTERVIEW_CONFIG;
    const questions = config.questions || [];
    const totalQuestions = config.totalQuestions || questions.length;
    const sessionId = config.sessionId;

    let currentIndex = 0;
    let elapsedSeconds = 0;
    let timerInterval = null;
    let speechRecognition = null;
    let isRecording = false;

    // DOM Elements
    const timerDisplay = document.getElementById('timerDisplay');
    const progressStepText = document.getElementById('progressStepText');
    const progressPercentText = document.getElementById('progressPercentText');
    const progressFill = document.getElementById('progressFill');

    const currentQuestionPill = document.getElementById('currentQuestionPill');
    const questionPromptText = document.getElementById('questionPromptText');
    const userAnswerText = document.getElementById('userAnswerText');
    const wordCountBadge = document.getElementById('wordCountBadge');

    const speechToggleBtn = document.getElementById('speechToggleBtn');
    const speechBtnLabel = document.getElementById('speechBtnLabel');
    const recordingBanner = document.getElementById('recordingBanner');

    const submitAnswerBtn = document.getElementById('submitAnswerBtn');
    const submitBtnText = document.getElementById('submitBtnText');
    const evalSpinner = document.getElementById('evalSpinner');

    const evaluationPanel = document.getElementById('evaluationPanel');
    const nextQuestionBtn = document.getElementById('nextQuestionBtn');
    const endInterviewEarlyBtn = document.getElementById('endInterviewEarlyBtn');

    // Start Timer
    startTimer();

    // Initialize Web Speech API
    initSpeechRecognition();

    // Render First Question
    loadCurrentQuestion();

    // Listeners
    if (userAnswerText) {
        userAnswerText.addEventListener('input', updateWordCount);
    }

    if (submitAnswerBtn) {
        submitAnswerBtn.addEventListener('click', handleAnswerSubmission);
    }

    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', handleNextQuestion);
    }

    if (endInterviewEarlyBtn) {
        endInterviewEarlyBtn.addEventListener('click', handleEarlyFinish);
    }

    // Model Answer Accordion Toggle
    const toggleModelBtn = document.getElementById('toggleModelAnswerBtn');
    const modelAnswerBody = document.getElementById('modelAnswerBody');
    if (toggleModelBtn && modelAnswerBody) {
        toggleModelBtn.addEventListener('click', () => {
            if (modelAnswerBody.style.display === 'none' || !modelAnswerBody.style.display) {
                modelAnswerBody.style.display = 'block';
                toggleModelBtn.querySelector('.toggle-indicator').textContent = '▲';
            } else {
                modelAnswerBody.style.display = 'none';
                toggleModelBtn.querySelector('.toggle-indicator').textContent = '▼';
            }
        });
    }

    /* -------------------------------------------------------------
       Timer Operations
       ------------------------------------------------------------- */
    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            elapsedSeconds++;
            const mins = String(Math.floor(elapsedSeconds / 60)).padStart(2, '0');
            const secs = String(elapsedSeconds % 60).padStart(2, '0');
            if (timerDisplay) {
                timerDisplay.textContent = `${mins}:${secs}`;
            }
        }, 1000);
    }

    /* -------------------------------------------------------------
       Word Count Tracker
       ------------------------------------------------------------- */
    function updateWordCount() {
        if (!userAnswerText || !wordCountBadge) return;
        const text = userAnswerText.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        wordCountBadge.textContent = `${words} words`;
    }

    /* -------------------------------------------------------------
       Web Speech API (Speech to Text)
       ------------------------------------------------------------- */
    function initSpeechRecognition() {
        if (!speechToggleBtn) return;

        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            speechToggleBtn.title = 'Speech Recognition is not supported in this browser. Please use Chrome/Edge.';
            speechToggleBtn.addEventListener('click', () => {
                alert('Your current browser does not support the Web Speech API. Please type your response directly or open this page in Google Chrome / Microsoft Edge.');
            });
            return;
        }

        speechRecognition = new SpeechRec();
        speechRecognition.continuous = true;
        speechRecognition.interimResults = true;
        speechRecognition.lang = 'en-US';

        speechRecognition.onresult = (event) => {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                }
            }
            if (finalTranscript && userAnswerText) {
                userAnswerText.value += (userAnswerText.value ? ' ' : '') + finalTranscript.trim();
                updateWordCount();
            }
        };

        speechRecognition.onerror = (event) => {
            console.warn('[Speech API Error]:', event.error);
            stopRecording();
        };

        speechRecognition.onend = () => {
            if (isRecording) {
                stopRecording();
            }
        };

        speechToggleBtn.addEventListener('click', () => {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        });
    }

    function startRecording() {
        if (!speechRecognition) return;
        try {
            speechRecognition.start();
            isRecording = true;
            speechToggleBtn.classList.add('recording');
            speechBtnLabel.textContent = 'Stop Dictation';
            if (recordingBanner) recordingBanner.classList.remove('d-none');
        } catch (e) {
            console.error(e);
        }
    }

    function stopRecording() {
        if (!speechRecognition) return;
        try {
            speechRecognition.stop();
        } catch (e) {}
        isRecording = false;
        speechToggleBtn.classList.remove('recording');
        speechBtnLabel.textContent = 'Record Voice';
        if (recordingBanner) recordingBanner.classList.add('d-none');
    }

    /* -------------------------------------------------------------
       Load Question UI
       ------------------------------------------------------------- */
    function loadCurrentQuestion() {
        if (currentIndex >= questions.length) return;

        const q = questions[currentIndex];
        const stepNum = currentIndex + 1;

        if (currentQuestionPill) currentQuestionPill.textContent = `Question ${stepNum}`;
        if (questionPromptText) questionPromptText.textContent = q.question_text;
        if (progressStepText) progressStepText.textContent = `Question ${stepNum} of ${totalQuestions}`;

        const pct = Math.round((currentIndex / totalQuestions) * 100);
        if (progressPercentText) progressPercentText.textContent = `${pct}% Complete`;
        if (progressFill) progressFill.style.width = `${pct}%`;

        // Clear answer workspace
        if (userAnswerText) {
            userAnswerText.value = '';
            userAnswerText.disabled = false;
            userAnswerText.focus();
        }
        updateWordCount();

        // Hide evaluation panel
        if (evaluationPanel) evaluationPanel.classList.add('d-none');
        if (submitAnswerBtn) {
            submitAnswerBtn.disabled = false;
            submitBtnText.textContent = 'Submit & Evaluate with AI →';
        }
    }

    /* -------------------------------------------------------------
       Submit Answer to AI Evaluator Endpoint
       ------------------------------------------------------------- */
    async function handleAnswerSubmission() {
        if (isRecording) stopRecording();

        const answer = userAnswerText.value.trim();
        if (!answer) {
            alert('Please provide an answer before submitting for AI evaluation.');
            userAnswerText.focus();
            return;
        }

        const currentQ = questions[currentIndex];

        // UI Loading state
        submitAnswerBtn.disabled = true;
        evalSpinner.classList.remove('d-none');
        submitBtnText.textContent = 'Analyzing with AI...';
        userAnswerText.disabled = true;

        try {
            const response = await fetch(`/api/interview/${sessionId}/submit-answer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question_id: currentQ.id,
                    answer: answer
                })
            });

            if (!response.ok) {
                throw new Error('Failed to evaluate response');
            }

            const data = await response.json();
            renderEvaluationScorecard(data);

        } catch (err) {
            console.error(err);
            alert('An error occurred during evaluation. Please try submitting again.');
            submitAnswerBtn.disabled = false;
            userAnswerText.disabled = false;
        } finally {
            evalSpinner.classList.add('d-none');
            submitBtnText.textContent = 'Answer Evaluated ✓';
        }
    }

    /* -------------------------------------------------------------
       Render AI Evaluation Scorecard
       ------------------------------------------------------------- */
    function renderEvaluationScorecard(data) {
        if (!evaluationPanel) return;

        // Overall Score
        const evalOverallScore = document.getElementById('evalOverallScore');
        if (evalOverallScore) evalOverallScore.textContent = data.scores.overall;

        // Pillar Meters
        const setMeter = (scoreElemId, barElemId, val) => {
            const sElem = document.getElementById(scoreElemId);
            const bElem = document.getElementById(barElemId);
            if (sElem) sElem.textContent = `${val}%`;
            if (bElem) bElem.style.width = `${val}%`;
        };

        setMeter('evalTechScore', 'evalTechBar', data.scores.technical);
        setMeter('evalClarityScore', 'evalClarityBar', data.scores.clarity);
        setMeter('evalCompletenessScore', 'evalCompletenessBar', data.scores.completeness);

        // Feedback Text
        const summaryText = document.getElementById('evalSummaryText');
        const strengthsText = document.getElementById('evalStrengthsText');
        const improvementsText = document.getElementById('evalImprovementsText');
        const modelAnswerText = document.getElementById('evalModelAnswerText');

        if (summaryText) summaryText.textContent = data.feedback;
        if (strengthsText) strengthsText.textContent = data.strengths;
        if (improvementsText) improvementsText.textContent = data.improvements;
        if (modelAnswerText) modelAnswerText.textContent = data.model_answer;

        // Keywords Tags
        const matchedContainer = document.getElementById('matchedKwTags');
        if (matchedContainer) {
            matchedContainer.innerHTML = '';
            if (data.matched_keywords && data.matched_keywords.length > 0) {
                data.matched_keywords.forEach(kw => {
                    const chip = document.createElement('span');
                    chip.className = 'kw-chip matched';
                    chip.textContent = `✓ ${kw}`;
                    matchedContainer.appendChild(chip);
                });
            } else {
                matchedContainer.innerHTML = '<span class="text-muted text-xs">No primary keywords detected</span>';
            }
        }

        const missingContainer = document.getElementById('missingKwTags');
        if (missingContainer) {
            missingContainer.innerHTML = '';
            if (data.missing_keywords && data.missing_keywords.length > 0) {
                data.missing_keywords.forEach(kw => {
                    const chip = document.createElement('span');
                    chip.className = 'kw-chip missing';
                    chip.textContent = `Missing: ${kw}`;
                    missingContainer.appendChild(chip);
                });
            } else {
                missingContainer.innerHTML = '<span class="text-success text-xs">All key concepts covered!</span>';
            }
        }

        // Configure Next Button
        if (currentIndex === totalQuestions - 1) {
            nextQuestionBtn.textContent = 'Complete Interview & View Final Scorecard →';
        } else {
            nextQuestionBtn.textContent = 'Next Question →';
        }

        // Reveal panel and scroll down smoothly
        evaluationPanel.classList.remove('d-none');
        evaluationPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /* -------------------------------------------------------------
       Next Question Navigation / Completion
       ------------------------------------------------------------- */
    function handleNextQuestion() {
        if (currentIndex < totalQuestions - 1) {
            currentIndex++;
            loadCurrentQuestion();
            const ws = document.getElementById('workspaceCard');
            if (ws) ws.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            finalizeInterviewSession();
        }
    }

    function handleEarlyFinish() {
        if (confirm('Are you sure you want to conclude this interview session early? Your answered questions will be scored.')) {
            finalizeInterviewSession();
        }
    }

    async function finalizeInterviewSession() {
        if (timerInterval) clearInterval(timerInterval);
        if (isRecording) stopRecording();

        if (nextQuestionBtn) {
            nextQuestionBtn.disabled = true;
            nextQuestionBtn.textContent = 'Finalizing Scorecard...';
        }

        try {
            const response = await fetch(`/api/interview/${sessionId}/finish`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    duration_seconds: elapsedSeconds
                })
            });

            const result = await response.json();
            if (result.redirect_url) {
                window.location.href = result.redirect_url;
            } else {
                window.location.href = `/results/${sessionId}`;
            }
        } catch (e) {
            console.error(e);
            window.location.href = `/results/${sessionId}`;
        }
    }
}
