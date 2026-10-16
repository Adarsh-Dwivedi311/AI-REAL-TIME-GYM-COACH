
import time
import streamlit as st
import base64


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0
        self.cooldown_seconds = 8

    def _find_form_issue(self, exercise, metrics):
        if not isinstance(metrics, dict):
            return None

        if metrics.get("issue"):
            return str(metrics["issue"])

        if exercise == "Squats":
            if metrics.get("depth_status") == "TOO HIGH":
                return "Squat depth is too shallow."
            angle = metrics.get("back_angle")
            if isinstance(angle, (int, float)) and angle < 130:
                return "Leaning too far forward during the squat."

        elif exercise == "Push-ups":
            if metrics.get("body_alignment") == "Poor Form":
                return "Body alignment is not straight during the push-up."
            if metrics.get("hip_status") == "SAGGING":
                return "Hips are sagging during the push-up."
            if metrics.get("hip_status") == "PIKED UP":
                return "Hips are too high during the push-up."

        elif exercise == "Biceps Curls (Dumbbell)":
            if metrics.get("swing_status") == "SWINGING":
                return "Torso is swinging during the biceps curl."
            if metrics.get("shoulder_status") == "ELBOW DRIFTING":
                return "Elbows are drifting away from the body."

        elif exercise == "Shoulder Press":
            if metrics.get("back_arch_status") == "Excessive Arch":
                return "Lower back is arching excessively."
            if metrics.get("back_arch_status") == "Slight Arch":
                return "Brace the core to reduce the back arch."

        elif exercise == "Lunges":
            if metrics.get("balance_status") == "OFF BALANCE":
                return "Balance is unstable during the lunge."

        return None

    def process_event(self, event, exercise, metrics=None):
        metrics = metrics or {}
        issue = self._find_form_issue(exercise, metrics)
        now = time.time()

        major_events = {
            "workout_started",
            "set_completed",
            "workout_completed",
        }

        if event not in major_events:
            # Live feedback is generated only when a form issue is detected.
            if not issue:
                return None

            if now - self.last_spoken_at < self.cooldown_seconds:
                return None

        try:
            feedback = self.llm.give_feedback(
                event=event,
                issue=issue,
            )
            audio_bytes = self.tts.speak(feedback)

            self.last_spoken_at = time.time()
            return audio_bytes, feedback

        except Exception as exc:
            # Show the actual error rather than silently hiding it.
            st.session_state["coach_error"] = str(exc)
            return None


        
def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return

    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    st.components.v1.html(
        f"""
        <audio autoplay>
            <source
                src="data:audio/mpeg;base64,{audio_base64}"
                type="audio/mpeg"
            />
        </audio>
        """,
        height=0,
    )
