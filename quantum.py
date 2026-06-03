"""Quantum-inspired sentiment layer.

Encodes a classical TextBlob polarity score onto a single qubit and *measures*
the probability of the review being "positive" on a real quantum simulator
(qiskit-aer's AerSimulator). This realizes the app's "probabilistic nature of
human emotions" idea with an actual quantum circuit rather than marketing copy.
"""

import math

# qiskit / qiskit-aer are heavy to import (several seconds). We defer importing
# them until the first sentiment computation so that app boot — and health
# checks — stay fast (important for cold starts on Render/HF Spaces).
_SIMULATOR = None

# Default number of measurement shots. More shots -> smoother probabilities.
DEFAULT_SHOTS = 1024


def _get_simulator():
    """Lazily build (and cache) the Aer simulator on first use."""
    global _SIMULATOR
    if _SIMULATOR is None:
        from qiskit_aer import AerSimulator

        _SIMULATOR = AerSimulator()
    return _SIMULATOR


def polarity_to_angle(polarity: float) -> float:
    """Map a TextBlob polarity in [-1, 1] to a qubit rotation angle in [0, pi].

    polarity = -1 -> theta = 0     (qubit stays |0>, always "negative")
    polarity =  0 -> theta = pi/2  (equal superposition, 50/50)
    polarity = +1 -> theta = pi    (qubit flips to |1>, always "positive")
    """
    polarity = max(-1.0, min(1.0, float(polarity)))
    return (polarity + 1.0) / 2.0 * math.pi


def measure_positive_probability(polarity: float, shots: int = DEFAULT_SHOTS) -> float:
    """Run a 1-qubit Ry circuit on the Aer simulator and return measured P(|1>).

    The probability of measuring |1> ("positive") is sin^2(theta / 2), and we
    estimate it empirically from `shots` measurements so the value genuinely
    comes from the quantum simulator.
    """
    from qiskit import QuantumCircuit

    theta = polarity_to_angle(polarity)

    circuit = QuantumCircuit(1, 1)
    circuit.ry(theta, 0)
    circuit.measure(0, 0)

    result = _get_simulator().run(circuit, shots=shots).result()
    counts = result.get_counts()

    positive_counts = counts.get("1", 0)
    return positive_counts / shots


def quantum_sentiment(polarity: float, shots: int = DEFAULT_SHOTS) -> dict:
    """Classify sentiment using the measured quantum probability.

    Returns a dict with the measured positive/negative probabilities and a
    label. Thresholds give a neutral band around the 50/50 superposition.
    """
    p_positive = measure_positive_probability(polarity, shots=shots)
    p_negative = 1.0 - p_positive

    if p_positive > 0.6:
        label = "Positive"
    elif p_positive < 0.4:
        label = "Negative"
    else:
        label = "Neutral"

    # Uncertainty peaks at a 50/50 superposition and is zero when the qubit
    # collapses cleanly to |0> or |1>. This is the app's "emotional ambiguity".
    uncertainty = 1.0 - abs(2.0 * p_positive - 1.0)

    return {
        "p_positive": p_positive,
        "p_negative": p_negative,
        "label": label,
        "uncertainty": uncertainty,
    }
