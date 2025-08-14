import logging
from typing import Dict, Tuple, Optional, Any, Set


class ProgressOrchestrator:
	"""
	Central authority for computing overall_progress from phase/submodule progress updates.
	- Defines monotonic phase ranges
	- Aggregates submodule steps across total submodules
	- Clamps overall progress to be non-decreasing
	"""

	def __init__(self) -> None:
		self.logger = logging.getLogger("progress.orchestrator")
		# Phase ranges as absolute [start, end] of overall progress
		# These are monotonic and disjoint to avoid overlap-induced regressions
		self.phase_ranges: Dict[str, Tuple[float, float]] = {
			"initialization": (0.00, 0.10),
			"search": (0.10, 0.30),
			"research_evaluation": (0.30, 0.40),
			"module_creation": (0.40, 0.55),
			"submodule_planning": (0.55, 0.60),
			"topic_resources": (0.60, 0.65),
			"submodules": (0.65, 0.95),
			"module_resources": (0.95, 0.97),
			"final_assembly": (0.97, 1.00),
		}
		# Internal phase progress [0..1] per unified phase
		self.phase_progress: Dict[str, float] = {k: 0.0 for k in self.phase_ranges.keys()}

		# Track totals
		self.total_modules: Optional[int] = None
		self.total_submodules: Optional[int] = None

		# Submodule step tracking: key "m:s" -> step_name -> progress [0..1]
		self.submodule_steps: Dict[str, Dict[str, float]] = {}
		self.known_submodules: Set[str] = set()

		# Weights for submodule steps (sum to 1.0)
		# Exclude submodule resource extraction due to missing granular IDs in some events
		self.submodule_step_weights: Dict[str, float] = {
			"research": 0.28,
			"content": 0.50,
			"content_refinement": 0.17,
			"quiz": 0.05,
		}

		# Internal tracking of composite sub-phases
		self._search_internal: float = 0.0  # composed from search_queries(30%) + web_searches(70%)
		self._research_eval_internal: float = 0.0  # composed from evaluation/refinement cycle

		# Monotonic overall
		self.current_overall: float = 0.0

	def declare_totals(self, total_modules: Optional[int] = None, total_submodules: Optional[int] = None) -> None:
		if total_modules is not None:
			self.total_modules = max(0, int(total_modules))
		if total_submodules is not None:
			self.total_submodules = max(0, int(total_submodules))

	def _update_phase_direct(self, phase: str, progress01: Optional[float], action: Optional[str]) -> None:
		if phase not in self.phase_ranges:
			return
		p = self._progress_from_action(progress01, action)
		self.phase_progress[phase] = max(self.phase_progress.get(phase, 0.0), p)

	def _progress_from_action(self, progress01: Optional[float], action: Optional[str]) -> float:
		if action == "completed":
			return 1.0
		if action == "started":
			return 0.0
		# processing or None: use provided or default midpoint
		return max(0.0, min(1.0, progress01 if progress01 is not None else 0.5))

	def _update_search(self, subphase: str, phase_progress: Optional[float]) -> None:
		# Normalize to [0..1] across both subphases
		pp = max(0.0, min(1.0, phase_progress or 0.0))
		if subphase == "search_queries":
			contrib = 0.3 * pp
		elif subphase == "web_searches":
			contrib = 0.3 + 0.7 * pp
		else:
			return
		self._search_internal = max(self._search_internal, min(1.0, contrib))
		self.phase_progress["search"] = max(self.phase_progress["search"], self._search_internal)

	def _update_research_eval(self, subphase: str, phase_progress: Optional[float], action: Optional[str], message: Optional[str]) -> None:
		pp = max(0.0, min(1.0, phase_progress or 0.0))
		if action == "completed" and message and "deemed sufficient" in message.lower():
			self._research_eval_internal = 1.0
		elif subphase == "research_evaluation":
			self._research_eval_internal = max(self._research_eval_internal, min(1.0, 0.33 * pp))
		elif subphase == "query_refinement":
			self._research_eval_internal = max(self._research_eval_internal, min(1.0, 0.33 + 0.33 * pp))
		elif subphase == "refinement_searches":
			self._research_eval_internal = max(self._research_eval_internal, min(1.0, 0.66 + 0.34 * pp))
		self.phase_progress["research_evaluation"] = max(self.phase_progress["research_evaluation"], self._research_eval_internal)

	def _ensure_submodule(self, module_id: int, sub_id: int) -> str:
		key = f"{module_id}:{sub_id}"
		if key not in self.submodule_steps:
			self.submodule_steps[key] = {k: 0.0 for k in self.submodule_step_weights.keys()}
			self.known_submodules.add(key)
			# If total is unknown, keep increasing to discovered size (monotonic aggregation)
			if self.total_submodules is None:
				self.total_submodules = len(self.known_submodules)
		return key

	def _map_phase_to_sub_step(self, phase: str) -> Optional[str]:
		if phase == "submodule_research":
			return "research"
		if phase in ("content_development",):
			return "content"
		if phase in ("content_evaluation", "content_refinement", "content_enhancement"):
			return "content_refinement"
		if phase == "quiz_generation":
			return "quiz"
		return None

	def _update_submodule_step(self, module_id: int, sub_id: int, phase: str, phase_progress: Optional[float], action: Optional[str]) -> None:
		step = self._map_phase_to_sub_step(phase)
		if step is None:
			return
		key = self._ensure_submodule(module_id, sub_id)
		p = self._progress_from_action(phase_progress, action)
		self.submodule_steps[key][step] = max(self.submodule_steps[key].get(step, 0.0), p)
		# Reflect into overall submodules phase
		self._recompute_submodules_phase()

	def _recompute_submodules_phase(self) -> None:
		if not self.submodule_steps:
			return
		den = self.total_submodules or len(self.submodule_steps)
		if den <= 0:
			return
		acc = 0.0
		for key, steps in self.submodule_steps.items():
			p_sub = 0.0
			for step, weight in self.submodule_step_weights.items():
				p_sub += weight * max(0.0, min(1.0, steps.get(step, 0.0)))
			acc += min(1.0, p_sub)
		avg = acc / max(1, den)
		self.phase_progress["submodules"] = max(self.phase_progress["submodules"], avg)

	def _extract_ids_from_preview(self, preview_data: Optional[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
		try:
			if not preview_data:
				return None
			data = preview_data.get("data") if isinstance(preview_data, dict) else None
			if not isinstance(data, dict):
				return None
			module_id = data.get("module_id")
			sub_id = data.get("submodule_id")
			if isinstance(module_id, int) and isinstance(sub_id, int):
				return module_id, sub_id
			return None
		except Exception:
			return None

	def _maybe_update_totals_from_preview(self, preview_data: Optional[Dict[str, Any]]) -> None:
		if not preview_data or not isinstance(preview_data, dict):
			return
		type_str = preview_data.get("type")
		data = preview_data.get("data") if isinstance(preview_data.get("data"), dict) else None
		if type_str == "modules_defined" and data:
			mods = data.get("modules")
			if isinstance(mods, list):
				self.total_modules = max(self.total_modules or 0, len(mods))
		elif type_str == "all_submodules_planned" and data:
			# Prefer explicit total
			if isinstance(data.get("total_submodules_planned"), int):
				self.total_submodules = max(self.total_submodules or 0, int(data.get("total_submodules_planned")))
			# Also capture modules count if present
			mods = data.get("modules")
			if isinstance(mods, list):
				self.total_modules = max(self.total_modules or 0, len(mods))
		elif type_str == "module_submodules_planned" and data:
			subs = data.get("submodules")
			if isinstance(subs, list):
				# Update discovered count conservatively if total not known
				discovered = len(self.known_submodules) + len(subs)
				if self.total_submodules is None:
					self.total_submodules = max(0, discovered)

	def update_event(self, *, message: Optional[str], phase: Optional[str], phase_progress: Optional[float], preview_data: Optional[Dict[str, Any]], action: Optional[str]) -> float:
		"""
		Update internal model from an incoming progress event and return the new monotonic overall.
		"""
		# Update totals if provided in preview
		self._maybe_update_totals_from_preview(preview_data)

		# Map incoming phase to orchestrator phases or submodule steps
		if phase in ("search_queries", "web_searches"):
			self._update_search(phase, phase_progress)
		elif phase in ("research_evaluation", "query_refinement", "refinement_searches"):
			self._update_research_eval(phase, phase_progress, action, message or "")
		elif phase == "modules":
			self._update_phase_direct("module_creation", phase_progress, action)
		elif phase == "submodule_planning":
			self._update_phase_direct("submodule_planning", phase_progress, action)
		elif phase == "topic_resources":
			self._update_phase_direct("topic_resources", phase_progress, action)
		elif phase == "module_resources":
			self._update_phase_direct("module_resources", phase_progress, action)
		elif phase == "final_assembly":
			self._update_phase_direct("final_assembly", phase_progress, action)
		elif phase == "initialization":
			self._update_phase_direct("initialization", phase_progress, action)
		# Submodule step phases
		elif phase in ("submodule_research", "content_development", "quiz_generation", "content_evaluation", "content_refinement", "content_enhancement"):
			ids = self._extract_ids_from_preview(preview_data)
			if ids:
				self._update_submodule_step(ids[0], ids[1], phase, phase_progress, action)
			else:
				# If no IDs present, ignore step-level mapping (cannot attribute)
				pass
		else:
			# Unknown or cosmetic phases do not affect overall
			pass

		# Compute absolute overall as the max across all phase contributions (ranges are monotonic and disjoint)
		overall_abs = self._compute_absolute_overall()
		# Monotonic clamp
		if overall_abs < self.current_overall:
			overall_abs = self.current_overall
		else:
			self.current_overall = overall_abs
		return self.current_overall

	def _compute_absolute_overall(self) -> float:
		vals = []
		for phase, (start, end) in self.phase_ranges.items():
			p = max(0.0, min(1.0, self.phase_progress.get(phase, 0.0)))
			vals.append(start + (end - start) * p)
		return max(vals) if vals else 0.0
