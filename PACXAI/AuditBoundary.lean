import PACXAI.Core

namespace PACXAI

structure DistillationCampaign (Secret Transcript Student Guess : Type) where
  population : Population Secret
  criterion : Criterion Secret Guess
  transcript : Observation Secret Transcript
  train : Transcript -> Student
  studentAttack : Student -> Guess

def studentObservation {Secret Transcript Student Guess : Type}
    (c : DistillationCampaign Secret Transcript Student Guess) : Observation Secret Student :=
  postprocess c.transcript c.train

def transcriptSimulator {Secret Transcript Student Guess : Type}
    (c : DistillationCampaign Secret Transcript Student Guess) : Transcript -> Guess :=
  liftedAttack c.train c.studentAttack

theorem student_attack_lifts_to_transcript {Secret Transcript Student Guess : Type}
    (c : DistillationCampaign Secret Transcript Student Guess) :
    successCount c.population c.criterion (fun s => c.studentAttack ((studentObservation c) s)) =
    successCount c.population c.criterion (fun s => (transcriptSimulator c) (c.transcript s)) := by
  rfl

theorem student_rate_lifts_to_transcript {Secret Transcript Student Guess : Type}
    (c : DistillationCampaign Secret Transcript Student Guess) :
    successRate c.population c.criterion (fun s => c.studentAttack ((studentObservation c) s)) =
    successRate c.population c.criterion (fun s => (transcriptSimulator c) (c.transcript s)) := by
  rfl

def conditionPopulation {Secret : Type}
    (secrets : Population Secret)
    (condition : Secret -> Bool) : Population Secret :=
  secrets.filter condition

theorem conditional_student_attack_lifts_to_transcript {Secret Transcript Student Guess : Type}
    (c : DistillationCampaign Secret Transcript Student Guess)
    (condition : Secret -> Bool) :
    successCount (conditionPopulation c.population condition) c.criterion
        (fun s => c.studentAttack ((studentObservation c) s)) =
    successCount (conditionPopulation c.population condition) c.criterion
        (fun s => (transcriptSimulator c) (c.transcript s)) := by
  rfl

abbrev CandidateAttack (Observation Guess : Type) := Observation -> Guess
abbrev CandidateClass (Obs Guess : Type) := List (CandidateAttack Obs Guess)

def observedSuccessCount {Secret Obs Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Obs)
    (attack : CandidateAttack Obs Guess) : Nat :=
  successCount secrets criterion (fun s => attack (obs s))

def candidateScores {Secret Obs Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Obs)
    (candidates : CandidateClass Obs Guess) : List Nat :=
  candidates.map (fun attack => observedSuccessCount secrets criterion obs attack)

def bestNat : List Nat -> Nat
  | [] => 0
  | x :: xs => Nat.max x (bestNat xs)

def candidateBestSuccess {Secret Obs Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Obs)
    (candidates : CandidateClass Obs Guess) : Nat :=
  bestNat (candidateScores secrets criterion obs candidates)

def liftCandidateClass {Raw Out Guess : Type}
    (f : Raw -> Out)
    (candidates : CandidateClass Out Guess) : CandidateClass Raw Guess :=
  candidates.map (liftedAttack f)

theorem candidateScores_postprocess_eq {Secret Raw Out Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Raw)
    (f : Raw -> Out)
    (candidates : CandidateClass Out Guess) :
    candidateScores secrets criterion (postprocess obs f) candidates =
    candidateScores secrets criterion obs (liftCandidateClass f candidates) := by
  induction candidates with
  | nil => rfl
  | cons a rest ih =>
      simp [candidateScores, liftCandidateClass, observedSuccessCount, postprocess, liftedAttack,
        successCount, countWhere]

theorem candidateBest_postprocess_eq_lifted {Secret Raw Out Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Raw)
    (f : Raw -> Out)
    (candidates : CandidateClass Out Guess) :
    candidateBestSuccess secrets criterion (postprocess obs f) candidates =
    candidateBestSuccess secrets criterion obs (liftCandidateClass f candidates) := by
  simp [candidateBestSuccess, candidateScores_postprocess_eq]

abbrev Code (A : Type) := A -> Nat

def observedCodeCost {Secret Obs : Type}
    (secrets : Population Secret)
    (obs : Observation Secret Obs)
    (code : Code Obs) : Nat :=
  (secrets.map (fun s => code (obs s))).foldl (fun acc n => acc + n) 0

def pullCode {A B : Type} (f : A -> B) (code : Code B) : Code A :=
  fun a => code (f a)

theorem deterministic_code_cost_exact {Secret Raw Out : Type}
    (secrets : Population Secret)
    (raw : Observation Secret Raw)
    (f : Raw -> Out)
    (outCode : Code Out) :
    observedCodeCost secrets (postprocess raw f) outCode =
    observedCodeCost secrets raw (pullCode f outCode) := by
  rfl

structure MonteCarloCertificate where
  samples : Nat
  successes : Nat
  allowedSuccesses : Nat
  deriving Repr, BEq

def MonteCarloCertificate.Passes (c : MonteCarloCertificate) : Prop :=
  c.successes <= c.allowedSuccesses

def monteCarloFromAttack {Secret Obs Guess : Type}
    (samples : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Obs)
    (attack : CandidateAttack Obs Guess)
    (allowedSuccesses : Nat) : MonteCarloCertificate :=
  { samples := samples.length,
    successes := observedSuccessCount samples criterion obs attack,
    allowedSuccesses := allowedSuccesses }

theorem monteCarlo_transcript_pass_implies_student_pass {Secret Raw Out Guess : Type}
    (samples : Population Secret)
    (criterion : Criterion Secret Guess)
    (raw : Observation Secret Raw)
    (f : Raw -> Out)
    (attack : CandidateAttack Out Guess)
    (allowedSuccesses : Nat)
    (h : (monteCarloFromAttack samples criterion raw (liftedAttack f attack) allowedSuccesses).Passes) :
    (monteCarloFromAttack samples criterion (postprocess raw f) attack allowedSuccesses).Passes := by
  exact h

end PACXAI
