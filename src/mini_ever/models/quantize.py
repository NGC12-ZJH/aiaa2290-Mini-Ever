"""Deployment copies: weight-only quantisation (test level L3).

Scheme ``weight_only_rtn``: every Conv2d / Linear / ArcFace weight is rounded
to the nearest value on a symmetric per-output-channel integer grid with
``bits`` bits, then stored back as floats. The resulting weights are *exactly*
the values an integer weight-only kernel would use, so the model's outputs
equal those of a weight-only INT8 / INT4 deployment up to accumulation order.
Activations stay in floating point; activation quantisation is out of scope
and must be reported as N/A if needed (protocol, 统计与结论).

This mirrors Zhang et al. (ICLR 2025), who found that round-to-nearest
weight quantisation can bring "unlearned" knowledge back in language models.
Whether the same happens in face models is an open question for Mini-Ever.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import torch
from torch import nn

from mini_ever.models.arcface import ArcFaceHead

SCHEME = "weight_only_rtn"


@dataclass(frozen=True)
class QuantizationReport:
    scheme: str
    bits: int
    quantized_tensors: int
    quantized_parameters: int
    mean_abs_error: float


def quantize_tensor(weight: torch.Tensor, bits: int) -> torch.Tensor:
    """Symmetric per-output-channel round-to-nearest quantisation (returns floats)."""
    if bits < 2:
        raise ValueError("bits must be >= 2")
    q_max = 2 ** (bits - 1) - 1
    flat = weight.detach().reshape(weight.shape[0], -1)
    scale = flat.abs().amax(dim=1, keepdim=True).clamp(min=1e-12) / q_max
    quantized = torch.clamp(torch.round(flat / scale), -q_max, q_max) * scale
    return quantized.reshape(weight.shape).to(weight.dtype)


def quantize_model(model: nn.Module, bits: int) -> tuple[nn.Module, QuantizationReport]:
    """Return a quantised deep copy of ``model`` and a report; ``model`` is untouched."""
    copy_ = copy.deepcopy(model)
    tensors = parameters = 0
    error_sum = 0.0
    with torch.no_grad():
        for module in copy_.modules():
            if isinstance(module, (nn.Conv2d, nn.Linear, ArcFaceHead)):
                original = module.weight.data
                quantized = quantize_tensor(original, bits)
                error_sum += (quantized - original).abs().sum().item()
                module.weight.data.copy_(quantized)
                tensors += 1
                parameters += original.numel()
    report = QuantizationReport(SCHEME, bits, tensors, parameters, error_sum / max(1, parameters))
    return copy_, report
