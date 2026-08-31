"""Assessment items for the data-analysis skills.

Each course's adaptive test reads the bank by skill, so a Data Analyst course
whose skills had no items would offer a test that cannot be graded. Every skill
added to the graph for this path is covered here, with difficulty spread across
at least three tiers so the adaptive engine has somewhere to move in both
directions.

The bar is the same as the rest of the bank: nothing that can be answered from
syntax trivia, and an explanation that teaches the misconception rather than
restating the answer. Several items are built around the specific mistakes this
path exists to catch — a `WHERE` that filters away the `NULL` side of a `LEFT
JOIN`, an aggregate whose row count is inflated by a fan-out join, a mean quoted
for a skewed distribution, and a truncated axis.
"""

from __future__ import annotations

from typing import Any

DATA_ITEMS: list[dict[str, Any]] = [
    # ---------------------------------------------------------- sql_basics
    {
        "id": "sql_basics_e1",
        "skill_id": "sql_basics",
        "difficulty": 2,
        "type": "mcq",
        "concept": "null handling",
        "prompt": (
            "A `notes` column is NULL for some rows. Which predicate matches "
            "exactly those rows?"
        ),
        "options": ["notes = NULL", "notes IS NULL", "notes == NULL", "notes = ''"],
        "correct_option": 1,
        "explanation": (
            "NULL means 'unknown', so `notes = NULL` evaluates to NULL rather than "
            "true and matches nothing. Only `IS NULL` tests for it. `= ''` is a "
            "different thing entirely: an empty string is a known value."
        ),
    },
    {
        "id": "sql_basics_e2",
        "skill_id": "sql_basics",
        "difficulty": 3,
        "type": "output_prediction",
        "concept": "where",
        "prompt": "How many rows does this return?",
        "code": (
            "-- orders: (1, 'paid'), (2, 'refunded'), (3, NULL), (4, 'paid')\n"
            "SELECT id FROM orders WHERE status != 'refunded';"
        ),
        "expected_answer": "2",
        "answer_checks": [r"^\s*2\s*$"],
        "explanation": (
            "Rows 1 and 4 match. Row 3 does not: `NULL != 'refunded'` is NULL, not "
            "true, so a comparison silently drops unknown values. Write "
            "`status IS NULL OR status != 'refunded'` if you meant to keep it."
        ),
    },
    {
        "id": "sql_basics_m1",
        "skill_id": "sql_basics",
        "difficulty": 5,
        "type": "mcq",
        "concept": "distinct",
        "prompt": (
            "`SELECT DISTINCT city, name FROM customers` returns more rows than "
            "`SELECT DISTINCT city FROM customers`. Why?"
        ),
        "options": [
            "DISTINCT only applies to the first column listed",
            "DISTINCT de-duplicates whole rows, so adding a column makes rows differ",
            "DISTINCT is ignored when more than one column is selected",
            "The second query has a syntax error and returns fewer rows by default",
        ],
        "correct_option": 1,
        "explanation": (
            "DISTINCT applies to the entire select list as one tuple. Two customers "
            "in the same city with different names are distinct rows, which is why "
            "`DISTINCT` is not a way to count unique cities once you add columns."
        ),
    },
    {
        "id": "sql_basics_m2",
        "skill_id": "sql_basics",
        "difficulty": 6,
        "type": "code_completion",
        "concept": "order by",
        "prompt": (
            "Return the `name` and `amount` of the three largest orders, biggest "
            "first, from a table `orders(id, name, amount)`."
        ),
        "expected_answer": "SELECT name, amount FROM orders ORDER BY amount DESC LIMIT 3;",
        "answer_checks": [
            r"(?is)select\s+name\s*,\s*amount",
            r"(?is)order\s+by\s+amount\s+desc",
            r"(?is)limit\s+3",
        ],
        "explanation": (
            "`LIMIT` without `ORDER BY` returns an arbitrary three rows: row order "
            "is undefined unless you ask for one. 'Top N' always means ORDER BY "
            "plus LIMIT."
        ),
    },
    # ----------------------------------------------------------- sql_joins
    {
        "id": "sql_joins_e1",
        "skill_id": "sql_joins",
        "difficulty": 3,
        "type": "mcq",
        "concept": "inner join",
        "prompt": (
            "You join `customers` to `orders` with an inner join to report per-"
            "customer totals. What happens to a customer who has never ordered?"
        ),
        "options": [
            "They appear with a total of 0",
            "They appear with a NULL total",
            "They do not appear at all",
            "The query fails with a foreign key error",
        ],
        "correct_option": 2,
        "explanation": (
            "An inner join keeps only rows with a match on both sides, so "
            "customers with no orders vanish — which is how a 'customer report' "
            "quietly becomes a 'customers who bought something' report. Use a LEFT "
            "JOIN when the unmatched side must survive."
        ),
    },
    {
        "id": "sql_joins_m1",
        "skill_id": "sql_joins",
        "difficulty": 6,
        "type": "code_debug",
        "concept": "left join",
        "prompt": (
            "This query is meant to list every customer along with their refunded "
            "orders, including customers with none. Customers with no refunds are "
            "missing. What is wrong, and how do you fix it?"
        ),
        "code": (
            "SELECT c.name, o.id\n"
            "FROM customers c\n"
            "LEFT JOIN orders o ON o.customer_id = c.id\n"
            "WHERE o.status = 'refunded';"
        ),
        "expected_answer": (
            "The WHERE clause runs after the join and discards the NULL rows the "
            "LEFT JOIN produced, turning it into an inner join. Move the condition "
            "into the ON clause: LEFT JOIN orders o ON o.customer_id = c.id AND "
            "o.status = 'refunded'."
        ),
        "answer_checks": [r"(?i)\bon\b", r"(?i)(where|filter)", r"(?i)(inner|null)"],
        "explanation": (
            "A filter on the right-hand table in `WHERE` is applied after the join "
            "has already invented NULL rows, and `NULL = 'refunded'` is not true — "
            "so those rows are dropped and the LEFT JOIN degrades to an inner join. "
            "Conditions on the optional side belong in `ON`."
        ),
    },
    {
        "id": "sql_joins_h1",
        "skill_id": "sql_joins",
        "difficulty": 8,
        "type": "output_prediction",
        "concept": "fan-out",
        "prompt": (
            "A customer has 1 row in `customers`, 3 rows in `orders` and 2 rows in "
            "`tickets`. Joining all three on customer_id, how many rows does this "
            "customer contribute?"
        ),
        "code": (
            "SELECT c.id\n"
            "FROM customers c\n"
            "JOIN orders  o ON o.customer_id = c.id\n"
            "JOIN tickets t ON t.customer_id = c.id;"
        ),
        "expected_answer": "6",
        "answer_checks": [r"^\s*6\s*$"],
        "explanation": (
            "Joining two independent one-to-many relationships multiplies them: "
            "3 × 2 = 6. This is fan-out, and it is why `SUM(o.amount)` in such a "
            "query silently double-counts revenue. Aggregate each branch separately "
            "(subqueries or CTEs) before joining them."
        ),
    },
    # ----------------------------------------------------- sql_aggregation
    {
        "id": "sql_agg_e1",
        "skill_id": "sql_aggregation",
        "difficulty": 3,
        "type": "mcq",
        "concept": "count",
        "prompt": (
            "`amount` is NULL for 4 of the 10 rows in `orders`. What do "
            "`COUNT(*)` and `COUNT(amount)` return?"
        ),
        "options": ["10 and 10", "10 and 6", "6 and 6", "10 and 4"],
        "correct_option": 1,
        "explanation": (
            "`COUNT(*)` counts rows; `COUNT(expr)` counts rows where the expression "
            "is not NULL. The same rule makes `AVG(amount)` an average over 6 "
            "values, not 10 — which is right or wrong depending on whether a "
            "missing amount means zero."
        ),
    },
    {
        "id": "sql_agg_m1",
        "skill_id": "sql_aggregation",
        "difficulty": 5,
        "type": "mcq",
        "concept": "having",
        "prompt": (
            "You need the cities whose total paid revenue exceeds 1000. Where does "
            "the `> 1000` condition go?"
        ),
        "options": [
            "In WHERE, alongside the status filter",
            "In HAVING, because it tests an aggregate computed per group",
            "In ORDER BY, using a threshold expression",
            "Either WHERE or HAVING — they are interchangeable",
        ],
        "correct_option": 1,
        "explanation": (
            "`WHERE` filters rows before grouping, so it cannot see `SUM(...)`. "
            "`HAVING` filters groups after aggregation. The status filter genuinely "
            "belongs in `WHERE`, because it is a row-level test — and putting it "
            "there is also faster, since fewer rows reach the grouping."
        ),
    },
    {
        "id": "sql_agg_m2",
        "skill_id": "sql_aggregation",
        "difficulty": 6,
        "type": "output_prediction",
        "concept": "group by",
        "prompt": (
            "The `orders` table is empty. How many rows does each of these return, "
            "in order?"
        ),
        "code": (
            "SELECT SUM(amount) FROM orders;\n"
            "SELECT city, SUM(amount) FROM orders GROUP BY city;"
        ),
        "expected_answer": "1 and 0",
        "answer_checks": [r"1\D+0"],
        "explanation": (
            "An ungrouped aggregate always returns exactly one row — here a single "
            "NULL. Add `GROUP BY` and there are no groups, so you get zero rows. "
            "A dashboard tile that reads the first row of the first query will "
            "display NULL where it should display 'no data'."
        ),
    },
    {
        "id": "sql_agg_h1",
        "skill_id": "sql_aggregation",
        "difficulty": 8,
        "type": "scenario",
        "concept": "average",
        "prompt": (
            "Your 'average order value by city' report shows a city with an "
            "average of £320 when every order there was £320 or less, and one "
            "order was refunded. Name two distinct causes to check."
        ),
        "expected_answer": (
            "Refunded orders are still included, so the filter on status is missing "
            "or wrong; and a fan-out join duplicated order rows, so the same order "
            "is counted several times, skewing the average. Check the status filter "
            "and the join cardinality."
        ),
        "answer_checks": [
            r"(?i)(status|refund|filter|where)",
            r"(?i)(join|duplicat|fan.?out|double)",
        ],
        "explanation": (
            "The two ways an aggregate lies are the wrong row set (a missing filter) "
            "and the wrong row count (a duplicating join). Verify both by comparing "
            "`COUNT(*)` against `COUNT(DISTINCT orders.id)`."
        ),
    },
    # ------------------------------------------------------- sql_analytics
    {
        "id": "sql_analytics_m1",
        "skill_id": "sql_analytics",
        "difficulty": 6,
        "type": "mcq",
        "concept": "window function",
        "prompt": (
            "What distinguishes `SUM(amount) OVER (PARTITION BY city)` from "
            "`SUM(amount) ... GROUP BY city`?"
        ),
        "options": [
            "Nothing — the window form is just newer syntax",
            "The window form keeps every input row and attaches the group total to each",
            "The window form is restricted to numeric columns",
            "The window form can only be used in an ORDER BY clause",
        ],
        "correct_option": 1,
        "explanation": (
            "`GROUP BY` collapses each group to one row. A window function computes "
            "over the partition while leaving the rows intact, which is what lets "
            "you put an order next to its city total (and compute 'share of city "
            "revenue') in a single pass."
        ),
    },
    {
        "id": "sql_analytics_m2",
        "skill_id": "sql_analytics",
        "difficulty": 7,
        "type": "mcq",
        "concept": "ranking",
        "prompt": (
            "Two products tie for second place by units sold. Which ranking "
            "function gives them both rank 2 and assigns rank 3 to the next "
            "product?"
        ),
        "options": ["ROW_NUMBER()", "RANK()", "DENSE_RANK()", "NTILE(3)"],
        "correct_option": 2,
        "explanation": (
            "`DENSE_RANK` shares the rank and continues without a gap (2, 2, 3). "
            "`RANK` shares it but skips (2, 2, 4). `ROW_NUMBER` breaks the tie "
            "arbitrarily, which makes 'top N' results non-deterministic between "
            "runs — the reason a top-N query needs a deterministic tiebreak."
        ),
    },
    {
        "id": "sql_analytics_h1",
        "skill_id": "sql_analytics",
        "difficulty": 8,
        "type": "code_completion",
        "concept": "cte",
        "prompt": (
            "Using a CTE, return each city and its revenue rank (1 = highest) from "
            "`orders(city, amount)`. Name the columns `city`, `revenue` and "
            "`revenue_rank`."
        ),
        "expected_answer": (
            "WITH totals AS (SELECT city, SUM(amount) AS revenue FROM orders GROUP BY city) "
            "SELECT city, revenue, RANK() OVER (ORDER BY revenue DESC) AS revenue_rank FROM totals;"
        ),
        "answer_checks": [
            r"(?is)with\s+\w+\s+as\s*\(",
            r"(?is)group\s+by\s+city",
            r"(?is)(rank|dense_rank|row_number)\s*\(\s*\)\s*over",
            r"(?is)order\s+by\s+revenue\s+desc",
        ],
        "explanation": (
            "Aggregate first, then rank the aggregates: a window function cannot "
            "take an aggregate of an aggregate in one level, so the totals need "
            "their own CTE (or subquery) before `RANK()` can order them."
        ),
    },
    # -------------------------------------------------------- data_cleaning
    {
        "id": "data_cleaning_e1",
        "skill_id": "data_cleaning",
        "difficulty": 4,
        "type": "mcq",
        "concept": "missing values",
        "prompt": (
            "A `discount` column is NULL for orders placed without a promo code. "
            "You are computing total discount given. What is the correct handling?"
        ),
        "options": [
            "Drop those rows, since the value is unknown",
            "Treat NULL as 0, because 'no promo code' means no discount was given",
            "Replace NULL with the column mean so the distribution is preserved",
            "Leave it — SUM already errors on NULL, which surfaces the problem",
        ],
        "correct_option": 1,
        "explanation": (
            "The right fill depends on what the NULL *means*. Here it encodes a "
            "known zero, so `COALESCE(discount, 0)` is correct. Dropping the rows "
            "would understate order count, and mean-imputation would invent "
            "discounts that were never given. Mean-filling is for genuinely "
            "missing measurements, not for absent-means-zero."
        ),
    },
    {
        "id": "data_cleaning_m1",
        "skill_id": "data_cleaning",
        "difficulty": 6,
        "type": "code_completion",
        "concept": "duplicates",
        "prompt": (
            "`events(user_id, event_id, occurred_at)` has the same `event_id` "
            "logged more than once. Return one row per `event_id`, keeping the "
            "earliest `occurred_at`."
        ),
        "expected_answer": (
            "SELECT event_id, MIN(occurred_at) AS occurred_at FROM events GROUP BY event_id;"
        ),
        "answer_checks": [
            r"(?is)(min\s*\(\s*occurred_at|row_number\s*\(\s*\)\s*over)",
            r"(?is)(group\s+by\s+event_id|partition\s+by\s+event_id)",
        ],
        "explanation": (
            "Deduplicating means naming the key and the rule for which row wins. "
            "`GROUP BY event_id` with `MIN` works when you only need the key and "
            "the timestamp; if you need whole rows, use "
            "`ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY occurred_at)` and "
            "keep rank 1. `SELECT DISTINCT` would not help here — the duplicate "
            "rows differ in other columns."
        ),
    },
    {
        "id": "data_cleaning_m2",
        "skill_id": "data_cleaning",
        "difficulty": 7,
        "type": "scenario",
        "concept": "type coercion",
        "prompt": (
            "A CSV column `amount` arrives as text: values like `1200`, `1,200`, "
            "`£1200` and an empty string. Sorting it puts `900` above `1200`. "
            "Explain the cause and what a safe conversion must do."
        ),
        "expected_answer": (
            "The column is still text, so it sorts lexicographically ('9' > '1'). "
            "A safe conversion strips the currency symbol and thousands separator, "
            "converts to a numeric type, and decides explicitly what an empty "
            "string becomes (NULL, not 0) — recording how many values failed to "
            "parse rather than silently coercing them."
        ),
        "answer_checks": [
            r"(?i)(text|string|lexic|alphabet)",
            r"(?i)(numeric|number|cast|convert|float|int)",
            r"(?i)(null|empty|fail|invalid|error)",
        ],
        "explanation": (
            "Text sorting is the tell that a numeric column was never converted. "
            "The dangerous part of the fix is the silent path: a conversion that "
            "turns unparseable values into 0 moves the error from a visible crash "
            "into a wrong total. Count and report the failures."
        ),
    },
    # -------------------------------------------------- exploratory_analysis
    {
        "id": "eda_e1",
        "skill_id": "exploratory_analysis",
        "difficulty": 4,
        "type": "mcq",
        "concept": "distribution",
        "prompt": (
            "Before quoting the average basket size, which single check tells you "
            "most about whether the average is meaningful?"
        ),
        "options": [
            "Whether the row count is above 1000",
            "How the values are distributed — its shape, spread and outliers",
            "Whether the column is stored as float rather than integer",
            "Whether the table has an index on the column",
        ],
        "correct_option": 1,
        "explanation": (
            "A mean summarises a distribution honestly only when the distribution "
            "is roughly symmetric and outlier-free. Basket sizes are usually "
            "right-skewed, so the mean sits above most baskets. Look at the shape "
            "(or at least the median and the percentiles) before quoting one number."
        ),
    },
    {
        "id": "eda_m1",
        "skill_id": "exploratory_analysis",
        "difficulty": 6,
        "type": "scenario",
        "concept": "segmentation",
        "prompt": (
            "Overall conversion is flat at 4% month over month, but the business "
            "changed its traffic mix. Name the analysis that would reveal a change "
            "hidden by the flat total, and what it looks for."
        ),
        "expected_answer": (
            "Segment the rate by channel (or cohort) and compare within segments. "
            "A flat total can hide conversion rising in every channel while the mix "
            "shifts toward a low-converting one — Simpson's paradox. Look at both "
            "the per-segment rates and the segment weights."
        ),
        "answer_checks": [
            r"(?i)(segment|cohort|channel|group|break ?down|split)",
            r"(?i)(mix|weight|composition|simpson|proportion)",
        ],
        "explanation": (
            "An aggregate is a weighted average of its segments, so it moves when "
            "either the rates or the weights move. Reporting only the total makes "
            "those two indistinguishable — and they call for opposite decisions."
        ),
    },
    {
        "id": "eda_h1",
        "skill_id": "exploratory_analysis",
        "difficulty": 8,
        "type": "mcq",
        "concept": "correlation",
        "prompt": (
            "Ice cream sales and drowning incidents correlate at r = 0.9 across "
            "months. What is the most defensible next step?"
        ),
        "options": [
            "Report the correlation as evidence that ice cream is dangerous",
            "Discard the finding, since correlation never carries information",
            "Look for a confounder — temperature drives both — and control for it",
            "Recompute with a larger sample until the correlation disappears",
        ],
        "correct_option": 2,
        "explanation": (
            "A strong correlation is a real observation and a bad conclusion. The "
            "analyst's job is to name the plausible common cause and check whether "
            "the association survives controlling for it — here it does not."
        ),
    },
    # -------------------------------------------------- statistics_business
    {
        "id": "stats_business_e1",
        "skill_id": "statistics_business",
        "difficulty": 5,
        "type": "mcq",
        "concept": "mean vs median",
        "prompt": (
            "Salaries in a team: 30k, 32k, 33k, 35k, 400k. Which summary should a "
            "report lead with, and why?"
        ),
        "options": [
            "The mean, because it uses every value",
            "The median, because one extreme value dominates the mean",
            "Either — with five values they are close enough",
            "The mode, because it is the most common salary",
        ],
        "correct_option": 1,
        "explanation": (
            "The mean here is 106k, which describes nobody: four of five people earn "
            "under 36k. The median (33k) is robust to the outlier. Quote the mean "
            "only alongside a spread measure, or when the distribution is symmetric."
        ),
    },
    {
        "id": "stats_business_m1",
        "skill_id": "statistics_business",
        "difficulty": 7,
        "type": "mcq",
        "concept": "significance",
        "prompt": (
            "An A/B test gives p = 0.03 on a 0.4% lift. What does the p-value "
            "actually tell you?"
        ),
        "options": [
            "There is a 3% chance the null hypothesis is true",
            "There is a 97% chance the variant is better",
            "A difference this large or larger would occur 3% of the time if there were no real effect",
            "The lift is 3% smaller than measured",
        ],
        "correct_option": 2,
        "explanation": (
            "A p-value is computed *assuming* no effect; it is not the probability "
            "that the null is true. And statistical significance is not business "
            "significance: a 0.4% lift may be real and still not worth shipping. "
            "Report the effect size and its confidence interval, not just p."
        ),
    },
    {
        "id": "stats_business_h1",
        "skill_id": "statistics_business",
        "difficulty": 9,
        "type": "scenario",
        "concept": "sampling",
        "prompt": (
            "A satisfaction survey emailed to all customers returns 800 responses "
            "with a 4.6/5 average. Marketing wants to publish '4.6 average "
            "satisfaction'. What is your objection, and what would you publish?"
        ),
        "expected_answer": (
            "The 800 respondents are self-selected, not a random sample: people "
            "with strong opinions (usually the satisfied and the furious) reply, so "
            "the mean measures respondents, not customers. Publish it as the "
            "respondent average with the response rate stated, and compare "
            "respondent characteristics against the customer base before "
            "generalising."
        ),
        "answer_checks": [
            r"(?i)(self.?select|response bias|non.?response|volunteer|not random|sampling bias)",
            r"(?i)(response rate|represent|generalis|generaliz|population)",
        ],
        "explanation": (
            "Sample size does not fix sample bias: 800 self-selected replies are not "
            "more representative than 80. The honest report states who was actually "
            "measured and at what response rate."
        ),
    },
    # --------------------------------------------------- data_visualization
    {
        "id": "data_viz_e1",
        "skill_id": "data_visualization",
        "difficulty": 3,
        "type": "mcq",
        "concept": "chart choice",
        "prompt": (
            "You are comparing total revenue across 8 product categories for one "
            "quarter. Which chart is the right default?"
        ),
        "options": [
            "A pie chart, since the parts make a whole",
            "A horizontal bar chart sorted by value",
            "A line chart with categories on the x axis",
            "A stacked area chart",
        ],
        "correct_option": 1,
        "explanation": (
            "Bars compare lengths on a common baseline, which humans read far more "
            "accurately than pie angles — and sorting makes the ranking readable at "
            "a glance. A line chart implies continuity between categories that does "
            "not exist; lines are for ordered dimensions like time."
        ),
    },
    {
        "id": "data_viz_m1",
        "skill_id": "data_visualization",
        "difficulty": 6,
        "type": "mcq",
        "concept": "axis truncation",
        "prompt": (
            "A bar chart of conversion (4.1% vs 4.3%) starts its y axis at 4.0% and "
            "the second bar looks twice as tall. What is the problem?"
        ),
        "options": [
            "Nothing — zooming in is how you make small differences visible",
            "Bar length encodes magnitude, so a non-zero baseline misstates the ratio",
            "The chart needs a logarithmic axis instead",
            "Percentages should never appear on a y axis",
        ],
        "correct_option": 1,
        "explanation": (
            "A bar's meaning is its length from zero, so truncating the axis "
            "exaggerates the difference — a 5% relative change reads as 100%. When "
            "the difference is genuinely small and matters, use a line or dot plot "
            "(where a non-zero axis is legitimate) and label the values."
        ),
    },
    {
        "id": "data_viz_m2",
        "skill_id": "data_visualization",
        "difficulty": 7,
        "type": "scenario",
        "concept": "encoding",
        "prompt": (
            "A chart plots 12 monthly values as 12 differently-coloured bars with a "
            "legend. Give two concrete improvements and say what each fixes."
        ),
        "expected_answer": (
            "Use one colour, because colour is encoding nothing — the x axis already "
            "carries the month, so 12 hues add noise and force a legend lookup. And "
            "keep months in chronological order along the axis (or use a line) so "
            "the trend is readable; reserve colour for a variable that actually "
            "varies, such as highlighting one month."
        ),
        "answer_checks": [
            r"(?i)(one colour|one color|single colour|single color|same colour|same color|remove.*legend|drop.*legend|colour is|color is)",
            r"(?i)(order|chronolog|line|trend|sort|time)",
        ],
        "explanation": (
            "Every visual channel should encode a variable. Colour that duplicates "
            "the x axis costs the reader a legend and buys nothing; the fix is to "
            "spend colour on the comparison you actually want noticed."
        ),
    },
    # ----------------------------------------------------- dashboard_design
    {
        "id": "dashboard_e1",
        "skill_id": "dashboard_design",
        "difficulty": 5,
        "type": "mcq",
        "concept": "kpi",
        "prompt": (
            "A dashboard shows 'Revenue: £84,210' as a single large number. What is "
            "the smallest addition that makes it actionable?"
        ),
        "options": [
            "A larger font and a brand colour",
            "A comparison — the period, and change against a baseline or target",
            "A second tile showing the same figure as a pie chart",
            "The underlying row count",
        ],
        "correct_option": 1,
        "explanation": (
            "A number with no reference point cannot be acted on: nobody knows "
            "whether £84,210 is good. The period it covers plus a delta against "
            "target or the prior period is what turns a readout into a decision."
        ),
    },
    {
        "id": "dashboard_m1",
        "skill_id": "dashboard_design",
        "difficulty": 7,
        "type": "scenario",
        "concept": "audience",
        "prompt": (
            "The same revenue data must serve a weekly exec review and an analyst "
            "investigating a dip. Why is one dashboard for both usually wrong, and "
            "what do you build instead?"
        ),
        "expected_answer": (
            "The two audiences need different granularity and different decisions: "
            "the exec needs a handful of KPIs with trend and target, the analyst "
            "needs segmentation and filters. One page serving both is either too "
            "dense to scan or too shallow to diagnose. Build a summary view whose "
            "tiles drill down into the detailed view, so the exec starts at the top "
            "and the analyst navigates deeper from the same numbers."
        ),
        "answer_checks": [
            r"(?i)(granular|detail|depth|dense|shallow|different (need|question|audience))",
            r"(?i)(drill|summary|overview|link|layer|two (view|page|level))",
        ],
        "explanation": (
            "Dashboard design is audience design. Layering — summary that drills "
            "into detail — serves both without forcing one of them to read the "
            "other's page, and keeps a single definition of each metric."
        ),
    },
    {
        "id": "dashboard_m2",
        "skill_id": "dashboard_design",
        "difficulty": 8,
        "type": "mcq",
        "concept": "narrative",
        "prompt": (
            "Two dashboards report 'active users' from the same warehouse and "
            "disagree by 11%. What is the first thing to establish?"
        ),
        "options": [
            "Which dashboard refreshes more often",
            "The metric definition each one uses — window, de-duplication and filters",
            "Whether one uses a bar chart and the other a line chart",
            "Which team owns each dashboard",
        ],
        "correct_option": 1,
        "explanation": (
            "Disagreeing numbers are almost always two different questions: 'active "
            "in the last 7 days' versus 'active this calendar week', distinct users "
            "versus sessions, internal accounts filtered or not. Until the "
            "definitions are written down, neither number can be defended."
        ),
    },
    # ------------------------------------------------- spreadsheet_modeling
    {
        "id": "spreadsheet_e1",
        "skill_id": "spreadsheet_modeling",
        "difficulty": 3,
        "type": "mcq",
        "concept": "absolute reference",
        "prompt": (
            "Cell `C2` holds `=B2*E1` where `E1` is the tax rate. Copied down to "
            "`C3`, it returns 0. Why?"
        ),
        "options": [
            "The formula needs to be re-entered manually in each row",
            "`E1` is a relative reference, so it became `E2`, which is empty",
            "Multiplication cannot be copied down a column",
            "`C3` must be formatted as a number first",
        ],
        "correct_option": 1,
        "explanation": (
            "Copying shifts relative references by the same offset, so the rate "
            "reference walks down into empty cells. Lock it as `$E$1` (or, better, "
            "name it) so every row multiplies by the one rate."
        ),
    },
    {
        "id": "spreadsheet_m1",
        "skill_id": "spreadsheet_modeling",
        "difficulty": 5,
        "type": "mcq",
        "concept": "lookup",
        "prompt": (
            "`VLOOKUP(A2, Products!A:D, 3, FALSE)` returns `#N/A` for rows you know "
            "exist in `Products`. Which cause is most likely?"
        ),
        "options": [
            "The range is too wide, so the lookup times out",
            "The lookup values differ in type or whitespace — text '1001' versus number 1001, or a trailing space",
            "`FALSE` forces an error whenever more than one match exists",
            "VLOOKUP cannot return the third column",
        ],
        "correct_option": 1,
        "explanation": (
            "Exact-match lookups fail on invisible differences: numbers stored as "
            "text, trailing spaces from an export, or inconsistent case in some "
            "tools. Normalise the key on both sides (TRIM, and a deliberate type "
            "conversion) before blaming the formula."
        ),
    },
    {
        "id": "spreadsheet_m2",
        "skill_id": "spreadsheet_modeling",
        "difficulty": 7,
        "type": "scenario",
        "concept": "scenario model",
        "prompt": (
            "You must hand over a revenue model where a reviewer can test three "
            "growth rates without editing formulas. Describe how you structure it."
        ),
        "expected_answer": (
            "Separate inputs from calculations: put the growth rate in one labelled "
            "input cell (or a small assumptions block), reference it absolutely from "
            "every formula, and never hardcode a number inside a formula. The "
            "reviewer then changes one cell and the whole model recalculates; a "
            "scenario table or data table can show all three side by side."
        ),
        "answer_checks": [
            r"(?i)(input|assumption|parameter).*(cell|block|sheet|separate)|separate.*(input|assumption)",
            r"(?i)(hardcod|hard-cod|absolute|\$|reference|one cell|single cell)",
        ],
        "explanation": (
            "The reason to isolate assumptions is auditability: a rate buried inside "
            "twelve formulas cannot be found, changed consistently, or reviewed. One "
            "labelled input referenced everywhere makes the model's assumptions "
            "explicit and its scenarios cheap."
        ),
    },
]
