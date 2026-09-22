# PawPal+ Project Reflection

## 1. System Design

**a. Initial design** 
My initial UML design breaks PawPal+ into five classes, separating the *data* (what a pet, owner, and task are) from the *behavior* (how a plan gets built and explained).

**`Owner`**
Holds the owner's basic info and preferences: name, the amount of time they have
available for pet care that day, and any scheduling preferences (e.g. preferred start time, whether they want high-priority tasks front-loaded). Responsible for storing the constraints the scheduler has to respect, and for owning one or more `Pet` objects.

**`Pet`**
Holds basic info about a single pet — name and species — and the list of `CareTask`
objects associated with that pet. Responsible for knowing what care the pet needs, and for adding/removing tasks from its own task list.

**`CareTask`**
Represents one unit of pet care (morning walk, feeding, medication, grooming,
enrichment). Stores a title, a duration in minutes, and a priority (low / medium /
high). Responsible for knowing its own cost in time and its importance, and for
converting priority into a numeric weight the scheduler can sort on.

**`Schedule`**
Represents the finished daily plan: an ordered list of scheduled tasks, each with a
start and end time, plus the set of tasks that had to be left out. Responsible for
holding the result of scheduling and for reporting totals (time used, time remaining, number of tasks included vs. skipped).

**`Scheduler`**
The class that does the actual work. Takes an `Owner` (with their time budget and
preferences) and a collection of `CareTask` objects, then selects and orders tasks that fit within the available time, prioritizing higher-priority tasks first. Responsible for producing a `Schedule` object and for generating an explanation of its decisions — why each task was included and placed where it was, and why any excluded task didn't make the cut.

**Why this split:** I kept `Scheduler` separate from `Owner` and `Pet` so the scheduling logic can be tested on its own without needing UI or a full object graph, and so the algorithm can be changed later without touching the data classes. `Schedule` exists as its own class rather than a plain list so the plan can carry its own summary and explanation data, which the Streamlit UI can display directly.

**b. Design changes**

Yes — a few changes came out of reviewing the class skeletons against the original UML:

- **Added a `ScheduledTask` class.** The original diagram had `Schedule.scheduled_tasks` typed as `list~ScheduledTask~` without `ScheduledTask` ever being defined, and my notes above describe "an ordered list of scheduled tasks, each with a start and end time" — which is more than a bare `CareTask` carries. `ScheduledTask` now pairs a `CareTask` with a `start_time` and `end_time`, and `Schedule` references it instead of referencing `CareTask` directly.
- **Gave `CareTask` a `pet_name` field.** `Owner.get_all_tasks()` flattens every pet's tasks into one list, which meant that once a task reached the `Scheduler` or `Schedule`, there was no way to say which pet it belonged to. `Pet.add_task()` will stamp this field when a task is added, so `Schedule.summary()` and `Scheduler.explain()` can still report per-pet detail after the flattening.
- **Added a `PRIORITY_WEIGHTS` lookup table on `CareTask`.** `priority_weight()` needs some mapping from `"low"/"medium"/"high"` to a sortable number; putting it as a class constant on `CareTask` keeps that mapping in one place instead of letting the scheduler hardcode its own copy.
- **`Scheduler` now stores the `Schedule` it builds.** The UML shows `Scheduler *-- Schedule : produces` as a composition, but the original skeleton only *returned* a `Schedule` from `build_schedule()` without keeping a reference. `Scheduler` now keeps `self.schedule`, so `explain()` has something to describe after the fact.
- **`Scheduler`'s task list now defaults to the owner's tasks.** The constructor originally defaulted `tasks` to an empty list when none was passed, which could quietly desync from what the owner's pets actually need. It now defaults to `owner.get_all_tasks()`, while still accepting an explicit list so the scheduling algorithm can be unit-tested without building a full `Owner`/`Pet` graph.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

`Scheduler.detect_time_conflicts()` only checks whether two tasks share the *exact same* `preferred_time` string (e.g. two tasks both set to `"07:00"`). It does not check whether their time **windows** actually overlap — a 30-minute walk starting at 07:00 and a 10-minute feeding starting at 07:15 both occupy
07:15, but the exact-match check won't flag them, because their
`preferred_time` values ("07:00" vs "07:15") don't match.

A full overlap check would compare every pair of tasks' `[start, start + duration)` ranges (an `O(n²)` scan, or `O(n log n)` with a sort-and-sweep), and it would also have to decide what to do about tasks with no fixed time at all, since those get placed wherever the greedy scheduler finds room. The exact-match version, by contrast, is a single pass that groups tasks into a
dict keyed by parsed time (`O(n)`), and its output is trivial to read: "these tasks want the *same* time," full stop — no minute-level interval math for the pet owner to interpret.

For PawPal+'s scale (a handful of tasks per pet per day, entered by hand), this tradeoff is reasonable: exact matches already catch the most common real mistake (re-adding a task at a time you already used, or two pets needing attention at once), it can never throw an exception since it just returns an
empty list when nothing collides, and the added complexity of true interval overlap detection isn't yet justified by how the app is actually used. If tasks start getting entered with tightly packed, slightly-offset times, this would be the first piece of scheduling logic worth upgrading to real interval
overlap checking.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
