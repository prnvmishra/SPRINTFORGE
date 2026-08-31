export type User = {
  id: string;
  name: string;
  email: string;
  avatar_url: string | null;
  bio?: string | null;
  auth_provider: string;
  is_onboarded: boolean;
  created_at: string;
};

export type LeaderboardEntry = {
  rank: number;
  user_id: string;
  name: string;
  avatar_url: string | null;
  score: number;
  xp: number;
  level: number;
  verified_skills: number;
  overall_confidence: number;
  is_current_user: boolean;
};

export type LeaderboardFormula = {
  expression: string;
  weights: Record<string, number>;
  caps: Record<string, number>;
  tie_break: string;
  components: { key: string; label: string; weight: number }[];
};

export type Leaderboard = {
  entries: LeaderboardEntry[];
  total: number;
  limit: number;
  offset: number;
  confidence_threshold: number;
  formula: LeaderboardFormula;
  current_user: LeaderboardEntry | null;
};

export type CommunityPost = {
  id: string;
  module_id: string;
  body: string;
  created_at: string;
  parent_id: string | null;
  author: { id: string; name: string; avatar_url: string | null };
  can_delete: boolean;
  replies: CommunityPost[];
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type ScoreBreakdown = {
  components?: Record<string, number>;
  weights?: Record<string, number>;
  effective_weights?: Record<string, number>;
  contributions?: Record<string, number>;
  active_channels?: string[];
  evidence_count?: number;
  evidence_factor?: number;
  expected_difficulty?: number;
  hardest_difficulty_passed?: number;
  limiting_factor?: string;
};

export type Skill = {
  skill_id: string;
  skill_name: string;
  claimed_level: string | null;
  verified_level: string;
  confidence: number;
  needs_improvement: boolean;
  weak_concepts: string[];
  breakdown: ScoreBreakdown;
  explanation: string;
  /** Jargon-free version of `explanation`, for first-time users. */
  plain_summary?: string;
  next_action?: {
    kind: "assessment" | "practice";
    label: string;
    skill_id: string;
    module_id: string | null;
  };
  difficulty_weight: number;
  evidence: Record<string, number>;
};

export type DigitalTwin = {
  user_id: string;
  goal: string | null;
  experience_level: string;
  claimed_skills: Record<string, string>;
  overall_confidence: number;
  xp: number;
  level: number;
  streak_days: number;
  consistency_score: number;
  learning_velocity: number;
  avg_completion_seconds: number;
  preferred_difficulty: number;
  completed_projects: number;
  repeated_mistakes: Record<string, number>;
  active_project_id: string | null;
  active_ticket_id: string | null;
  path_id: string | null;
  placement_status: PlacementStatus;
  verified_skills: Skill[];
  skills_needing_improvement: Skill[];
};

/* ------------------------------------------------------------------- placement */

/**
 * `unavailable` means the chosen path has no curriculum to probe yet, and
 * `skipped` means the learner declined. Neither is ever rendered as a pass.
 */
export type PlacementStatus =
  | "pending"
  | "in_progress"
  | "complete"
  | "skipped"
  | "unavailable";

export type PlacementProbe = {
  skill_id: string;
  skill_name: string;
  course_id: string;
  course_title: string;
  questions: number;
  session_id: string | null;
  status: "not_started" | "in_progress" | "complete";
  /** Null until the probe has been graded — never render it as a zero. */
  accuracy: number | null;
  verified_level: string | null;
  confidence: number | null;
  weak_concepts: string[];
  passed: boolean | null;
};

export type PlacementStartingPoint = {
  path_id: string;
  course_id: string;
  course_title: string;
  blurb: string;
  first_skill_id: string | null;
  first_skill_name: string | null;
  first_module_id: string | null;
};

export type PlacementResult = {
  level: "no_experience" | "early_basics" | "intermediate" | "advanced";
  accuracy: number;
  probes_graded: number;
  probes_passed: number;
  stopped_early: boolean;
  starting_point: PlacementStartingPoint | null;
  skip_courses: { course_id: string; course_title: string }[];
  summary: string;
};

export type PlacementState = {
  status: PlacementStatus;
  path_id: string | null;
  path_label: string | null;
  confidence_threshold: number;
  questions_per_probe: number;
  total_probes: number;
  probes_completed: number;
  probes: PlacementProbe[];
  next_probe: PlacementProbe | null;
  stopped_early: boolean;
  result: PlacementResult | null;
};

/** Read-only headline carried by the dashboard payload. */
export type PlacementSummary = {
  status: PlacementStatus;
  path_id: string | null;
  path_label: string | null;
  total_probes: number;
  probes_completed: number;
  next_probe: PlacementProbe | null;
  result: PlacementResult | null;
  required: boolean;
};

export type Recommendation = {
  type:
    | "remediation_practice"
    | "prerequisite_practice"
    | "practice"
    | "ticket"
    | "assessment"
    | "placement"
    | "project";
  skill_id: string | null;
  skill_name?: string;
  module_id?: string | null;
  ticket_id?: string;
  path_id?: string | null;
  title: string;
  reason: string;
  evidence: Record<string, unknown>;
  blocked_ticket?: { id: string; key: string; title: string } | null;
};

export type TicketStatus =
  | "locked"
  | "todo"
  | "in_progress"
  | "submitted"
  | "under_review"
  | "failed"
  | "done";

/**
 * Describes the cumulative project preview: which of the project's tickets are
 * verified, which files the rendered document is composed of, and whether the
 * host document had to be scaffolded because the project has no HTML yet.
 */
/**
 * A ticket the learner started but never got verified, whose files are layered
 * into the preview so half-built work is visible rather than invisible.
 */
export type InProgressContributor = {
  ticket_id: string;
  key: string;
  title: string;
  status: TicketStatus;
  files: string[];
  /** Always false — unverified work is never presented as shipped. */
  verified: false;
  incomplete: boolean;
};

export type PreviewMeta = {
  verified_tickets: number;
  total_tickets: number;
  files: string[];
  /** Every contributing ticket key, verified first then in-progress. */
  contributing_tickets: string[];
  verified_contributors: string[];
  in_progress_contributors: InProgressContributor[];
  unfinished_tickets: InProgressContributor[];
  includes_unverified: boolean;
  synthesized_host: boolean;
  mount_points: string[];
};

export type Ticket = {
  id: string;
  key: string;
  title: string;
  description: string;
  target_skill_id: string;
  target_skill_name: string;
  difficulty: number;
  requirements: string[];
  acceptance_criteria: string[];
  dependencies: string[];
  estimated_minutes: number;
  status: TicketStatus;
  lock_reason: string | null;
  xp_reward: number;
  order_index: number;
  sprint_id: string;
  attempt_count: number;
  files?: Record<string, string>;
  editable_files?: string[];
  project_id?: string;
  project_title?: string;
  sprint_name?: string;
  milestone?: string;
  preview?: string | null;
  preview_meta?: PreviewMeta;
  /**
   * Cumulative project files behind `preview` — the learner's own verified work
   * from earlier tickets. Held so the pane can be recomposed locally with the
   * live editor buffers on top, which is what makes a CSS-only ticket preview
   * as you type. Never sent back for grading.
   */
  preview_files?: Record<string, string>;
};

/** Whole-project preview response from `/projects/{id}/preview`. */
export type ProjectPreview = {
  project: { id: string; title: string; status: string; progress_percent: number };
  html: string | null;
  meta: PreviewMeta;
};

export type Sprint = {
  id: string;
  name: string;
  milestone: string;
  goal: string | null;
  status: string;
  order_index: number;
  tickets: Ticket[];
};

export type Project = {
  id: string;
  title: string;
  idea: string;
  tech_stack: string[];
  complexity: string;
  desired_outcome: string | null;
  status: string;
  progress_percent: number;
  plan_rationale: string | null;
  created_at: string;
  sprint_count: number;
  ticket_count: number;
  tickets_done: number;
  sprints?: Sprint[];
};

export type FailureAnalysis = {
  id: string;
  skill_id: string;
  skill_name: string;
  source_type: string;
  source_id: string | null;
  root_cause: string;
  missing_concepts: string[];
  explanation: string;
  remediation_module_id: string | null;
  remediation_title: string | null;
  resolved: boolean;
  created_at: string;
};

export type RewardSummary = {
  xp: number;
  level: number;
  xp_into_level: number;
  xp_for_next_level: number;
  streak_days: number;
  recent: {
    id: string;
    amount: number;
    reason: string;
    source_type: string;
    created_at: string;
  }[];
};

export type Dashboard = {
  user: User;
  twin: DigitalTwin;
  confidence_threshold: number;
  verified_skills: Skill[];
  skills_needing_improvement: Skill[];
  active_project: {
    id: string;
    title: string;
    status: string;
    progress_percent: number;
    tech_stack: string[];
    sprint_count: number;
    ticket_count: number;
    tickets_done: number;
  } | null;
  current_sprint: {
    id: string;
    name: string;
    milestone: string;
    status: string;
    ticket_count: number;
    tickets_done: number;
  } | null;
  current_ticket: Ticket | null;
  projects: { id: string; title: string; status: string; progress_percent: number; tech_stack: string[] }[];
  rewards: RewardSummary;
  placement: PlacementSummary;
  recommendation: Recommendation;
  open_gaps: FailureAnalysis[];
  recent_activity: {
    id: string;
    event_type: string;
    title: string;
    detail: string | null;
    created_at: string;
  }[];
};

export type CheckResult = {
  id: string;
  label: string;
  passed: boolean;
  hidden?: boolean;
  concept: string | null;
  hint?: string | null;
  detail?: string | null;
  /**
   * Which requirement this check grades, declared by the spec (zero-based).
   * `null` means it grades no single requirement; `undefined` means the spec
   * predates the mapping, so the client falls back to matching by wording.
   */
  requirement_index?: number | null;
  /** Set when one check covers several requirements. */
  requirement_indexes?: number[] | null;
  /** File-level precondition: never owns a requirement, never counted. */
  precondition?: boolean;
  /** True when the spec declared the mapping above, even if it declared none. */
  requirement_mapped?: boolean;
  /**
   * The check itself is broken (e.g. an unresolved `{entity}` placeholder in its
   * selector), so the submission was never examined. Rendered as a validator
   * configuration error, never as a failed requirement.
   */
  config_error?: boolean;
};

export type Evaluation = {
  is_correct: boolean;
  conceptual_mistake: string | null;
  next_difficulty: number;
  feedback: string;
  missing_concepts: string[];
  suggested_remediation: string | null;
  provider: string;
};

export type PracticeModuleSummary = {
  id: string;
  title: string;
  kind: "web" | "challenge";
  practice_layer: string;
  technology: string;
  skill_id: string;
  skill_name: string;
  difficulty: number;
  estimated_minutes: number;
  summary: string;
  is_remediation: boolean;
  xp_reward: number;
};

export type PracticeModule = PracticeModuleSummary & {
  language: string | null;
  problem_statement: string | null;
  constraints: string[];
  input_format: string | null;
  output_format: string | null;
  requirements: string[];
  files: Record<string, string>;
  editable_files: string[];
  entry_file: string | null;
  sample_tests: { name: string; stdin: string; expected_stdout: string }[];
  hidden_test_count: number;
  track: string | null;
  examples: { stdin: string; stdout: string; explanation: string }[];
};

export type CourseProgress = {
  skills_total: number;
  skills_verified: number;
  percent: number;
  complete: boolean;
};

export type CourseSummary = {
  id: string;
  path_id: string;
  title: string;
  blurb: string;
  skill_count: number;
  module_count: number;
  test_available: boolean;
  test_item_count: number;
  has_project: boolean;
  project_started_id: string | null;
  estimated_minutes: number;
  progress: CourseProgress;
};

export type PathSummary = {
  id: string;
  label: string;
  tagline: string;
  blurb: string;
  roles: string[];
  available: boolean;
  course_count: number;
  planned_courses: string[];
  progress: { courses_total: number; courses_completed: number; percent: number };
};

export type PathDetail = PathSummary & {
  courses: CourseSummary[];
  next_course_id: string | null;
};

export type CourseLesson = {
  order: number;
  skill_id: string;
  skill_name: string;
  confidence: number;
  verified: boolean;
  unlocked: boolean;
  missing_prerequisites: { skill_id: string; skill_name: string }[];
  item_count: number;
};

export type CourseTestPlan = {
  stages: { skill_id: string; skill_name: string; item_count: number; available: boolean }[];
  total_items: number;
  mode: string;
  available: boolean;
  unavailable_reason: string | null;
  pass_mark: number;
};

export type CourseDetail = {
  id: string;
  path_id: string;
  path_label: string;
  title: string;
  blurb: string;
  lessons: CourseLesson[];
  modules: {
    id: string;
    title: string;
    kind: string;
    technology: string;
    skill_id: string;
    skill_name: string;
    difficulty: number;
    estimated_minutes: number;
    hidden_test_count: number;
    xp_reward: number;
  }[];
  test: CourseTestPlan;
  project: {
    title: string;
    idea: string;
    tech_stack: string[];
    complexity: string;
    desired_outcome: string;
    existing_project_id: string | null;
  } | null;
  progress: CourseProgress;
  pass_mark: number;
};

export type SubmitResult = {
  attempt_id: string;
  passed: boolean;
  static_results: CheckResult[];
  test_results: CheckResult[];
  evaluation: Evaluation;
  xp_awarded: number;
  failure_analysis: FailureAnalysis | null;
  skill: { skill_id: string; skill_name: string; confidence: number; verified_level: string };
  overall_confidence: number;
  xp: number;
  level: number;
};

export type TicketSubmitResult = {
  attempt_id: string;
  ticket: Ticket;
  passed: boolean;
  static_results: CheckResult[];
  test_results?: CheckResult[];
  passed_count?: number;
  total_count?: number;
  tests_passed_count?: number;
  tests_total_count?: number;
  evaluation: Evaluation;
  xp_awarded: number;
  milestone_bonus: number;
  failure_analysis: FailureAnalysis | null;
  unlocked_tickets: { ticket_id: string; key: string; title: string }[];
  skill: { skill_id: string; skill_name: string; confidence: number; verified_level: string };
  overall_confidence: number;
  xp: number;
  level: number;
};

export type AssessmentQuestion = {
  id: string;
  skill_id: string;
  type: "mcq" | "output_prediction" | "code_debug" | "code_completion" | "scenario";
  difficulty: number;
  concept: string | null;
  prompt: string;
  code: string | null;
  options: string[] | null;
  language: string;
};

export type AssessmentState = {
  session_id: string;
  skill_id: string;
  status: string;
  questions_asked: number;
  max_questions: number;
  correct_count: number;
  current_difficulty: number;
  question: AssessmentQuestion | null;
  result: AssessmentResult | null;
};

export type AssessmentResult = {
  skill_id: string;
  skill_name: string;
  claimed_level: string | null;
  verified_level: string;
  accuracy: number;
  questions_answered: number;
  correct_count: number;
  hardest_difficulty_passed: number;
  weak_concepts: string[];
  gap_skills: { skill_id: string; skill_name: string }[];
  claim_matches_reality: boolean;
  timeline: {
    question_id: string;
    difficulty: number;
    concept: string | null;
    is_correct: boolean;
    feedback: string | null;
  }[];
};

export type AssessmentSubmitResponse = {
  is_correct: boolean;
  evaluation: Evaluation;
  state: AssessmentState;
  skill: {
    skill_id: string;
    skill_name: string;
    confidence: number;
    verified_level: string;
    weak_concepts: string[];
  };
  failure_analysis: FailureAnalysis | null;
};

export type MentorResponse = {
  answer: string;
  next_step: string | null;
  guiding_questions: string[];
  concepts: string[];
  reveals_solution: boolean;
  provider: string;
};

export type WhyThisNext = {
  recommendation: Recommendation;
  explanation: string;
  dependency_chain: {
    skill_id: string;
    skill_name: string;
    confidence: number;
    threshold: number;
  }[];
};

export type PrerequisiteGap = {
  skill_id: string;
  skill_name: string;
  confidence: number;
  required: number;
  difficulty_weight?: number;
  recommended_practice?: string[];
};

export type GraphNode = {
  id: string;
  name: string;
  track: string;
  difficulty_weight: number;
  prerequisites: string[];
  unlocks: string[];
  related_concepts: string[];
  recommended_practice: string[];
  confidence: number;
  has_evidence: boolean;
  unlocked: boolean;
  missing_prerequisites: PrerequisiteGap[];
};

/* ------------------------------------------------------------------ learning path */

/** Where a skill sits on the learner's route. `locked` means a prerequisite is unmet. */
export type PathSkillState = "verified" | "in_progress" | "not_started" | "locked";

export type LearningResource = {
  kind: "interactive_practice" | "challenge" | "assessment" | "course_lesson" | "concept_guide" | "documentation";
  title: string;
  /** Null when the duration is genuinely unknown, e.g. a course lesson. */
  minutes: number | null;
  target: "practice_module" | "assessment" | "course" | "external";
  /** Exactly one of these is set, matching `target`. */
  module_id?: string;
  skill_id?: string;
  path_id?: string;
  course_id?: string;
  url: string | null;
  item_count?: number;
  internal: boolean;
};

export type SkillResources = {
  skill_id: string;
  skill_name: string;
  known_skill: boolean;
  related_concepts: string[];
  resources: LearningResource[];
};

export type LearningPathGoal = {
  goal: string | null;
  experience_level: string;
  target_stack: string[];
  /** How the stack was derived, since the twin has no explicit stack field. */
  target_source: string;
  /** Ids into the existing /paths curriculum, for linking into course pages. */
  path_id: string | null;
  next_course_id: string | null;
  active_project_id: string | null;
  active_project_title: string | null;
};

export type LearningPathStep = {
  order: number;
  skill_id: string;
  skill_name: string;
  confidence: number;
  verified: boolean;
  unlocked: boolean;
  missing_prerequisites: PrerequisiteGap[];
  item_count: number;
  claimed_level: string | null;
  /** Null when the skill has no verified-skill record yet, i.e. never assessed. */
  verified_level: string | null;
  needs_improvement: boolean;
  has_evidence: boolean;
  weak_concepts: string[];
  has_open_gap: boolean;
  state: PathSkillState;
  prerequisites: string[];
  unlocks: string[];
  track: string;
  difficulty_weight: number;
  /** The existing course that teaches this skill, for deep-linking. */
  taught_by: { path_id: string; course_id: string } | null;
  is_next: boolean;
};

/**
 * `learning` milestones group skills by course; `execution` milestones group
 * project sprints. They are deliberately different things and are returned
 * separately.
 */
export type LearningMilestone = {
  name: string;
  kind: "learning" | "execution";
  path_id: string | null;
  course_id: string | null;
  status: "complete" | "in_progress" | "not_started" | "locked";
  skills: {
    skill_id: string;
    skill_name: string;
    confidence: number;
    verified: boolean;
    unlocked: boolean;
  }[];
  completed_count: number;
  total_count: number;
};

export type NextAction = Recommendation & {
  explanation: string;
  /** Honesty marker: the routing reason is rule-based, not model-generated. */
  reason_source: string;
  resources: LearningResource[];
};

export type LearningPath = {
  goal: LearningPathGoal;
  confidence_threshold: number;
  progress: { skills_total: number; skills_verified: number; percent: number };
  path: LearningPathStep[];
  milestones: LearningMilestone[];
  execution_milestones: LearningMilestone[];
  next_action: NextAction | null;
};

/* ------------------------------------------------------------------ adaptations */

export type AdaptationEvent = {
  id: string;
  at: string;
  event_type: string;
  title: string;
  trigger: string | null;
  skill_id: string | null;
  skill_name: string | null;
  /**
   * Null for events that predate confidence capture. `confidence_recorded`
   * distinguishes "unknown" from "no change" — never render a delta without it.
   */
  confidence_before: number | null;
  confidence_after: number | null;
  confidence_delta: number | null;
  confidence_recorded: boolean;
  inserted_skills: { skill_id: string; skill_name: string }[];
  recommendation: { skill_id: string | null; title: string; reason: string } | null;
  unlocked_tickets: { ticket_id: string; key: string; title: string }[];
  resolved_gaps: string[] | null;
  weak_concepts: string[];
  failure: {
    id: string;
    root_cause: string;
    missing_concepts: string[];
    remediation_module_id: string | null;
    remediation_title: string | null;
    resolved: boolean;
  } | null;
  source: { type: string; id: string | null };
};

export type Adaptations = {
  events: AdaptationEvent[];
  confidence_history_available_from: string;
};
