namespace PACXAI

abbrev Observation (Secret Output : Type) := Secret -> Output
abbrev Criterion (Secret Guess : Type) := Secret -> Guess -> Bool
abbrev Population (Secret : Type) := List Secret

def countWhere {A : Type} (xs : List A) (p : A -> Bool) : Nat :=
  (xs.filter p).length

def successCount {Secret Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (attack : Secret -> Guess) : Nat :=
  countWhere secrets (fun s => criterion s (attack s))

structure EmpiricalRate where
  numerator : Nat
  denominator : Nat
  deriving Repr, BEq

def successRate {Secret Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (attack : Secret -> Guess) : EmpiricalRate :=
  { numerator := successCount secrets criterion attack, denominator := secrets.length }

def passesBudget {Secret Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (budget : Nat)
    (attack : Secret -> Guess) : Prop :=
  successCount secrets criterion attack <= budget

def postprocess {Secret Raw Out : Type}
    (obs : Observation Secret Raw)
    (f : Raw -> Out) : Observation Secret Out :=
  fun s => f (obs s)

def liftedAttack {Raw Out Guess : Type}
    (f : Raw -> Out)
    (attack : Out -> Guess) : Raw -> Guess :=
  fun r => attack (f r)

theorem postprocess_successCount_eq {Secret Raw Out Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Raw)
    (f : Raw -> Out)
    (attack : Out -> Guess) :
    successCount secrets criterion (fun s => attack ((postprocess obs f) s)) =
    successCount secrets criterion (fun s => (liftedAttack f attack) (obs s)) := by
  rfl

theorem postprocess_successRate_eq {Secret Raw Out Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (obs : Observation Secret Raw)
    (f : Raw -> Out)
    (attack : Out -> Guess) :
    successRate secrets criterion (fun s => attack ((postprocess obs f) s)) =
    successRate secrets criterion (fun s => (liftedAttack f attack) (obs s)) := by
  rfl

theorem postprocess_budget_sound {Secret Raw Out Guess : Type}
    (secrets : Population Secret)
    (criterion : Criterion Secret Guess)
    (budget : Nat)
    (obs : Observation Secret Raw)
    (f : Raw -> Out)
    (attack : Out -> Guess)
    (h : passesBudget secrets criterion budget (fun s => (liftedAttack f attack) (obs s))) :
    passesBudget secrets criterion budget (fun s => attack ((postprocess obs f) s)) := by
  exact h

end PACXAI
