export const speak = (text, onEnd = null) => {
  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Remove HTML tags for clean speech
  const cleanText = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  utterance.lang = 'en-US';

  if (onEnd) {
    utterance.onend = onEnd;
  }

  window.speechSynthesis.speak(utterance);
};

export const stopSpeaking = () => {
  window.speechSynthesis.cancel();
};

export const isSpeaking = () => {
  return window.speechSynthesis.speaking;
};