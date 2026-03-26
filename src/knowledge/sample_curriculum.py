"""
Sample Curriculum Data Generator — Creates text-based curriculum files
for multiple subjects and topics to populate the knowledge base.
"""

import os

CURRICULA_DIR = os.path.join("data", "curricula")

CURRICULA = {
    "math": {
        "algebra": """## Algebra

### Variables and Expressions
Algebra uses letters (variables) to represent unknown numbers. An algebraic expression combines variables, numbers, and operations. For example, 3x + 5 is an expression where x is a variable.

### Linear Equations
A linear equation is an equation of the first degree, meaning the variable is raised to the power of 1. The general form is ax + b = 0. To solve, isolate the variable: x = -b/a.

Example: Solve 2x + 6 = 0 → 2x = -6 → x = -3.

### Quadratic Equations
A quadratic equation has the form ax² + bx + c = 0. Solutions can be found using:
- Factoring: Find two numbers that multiply to ac and add to b.
- Quadratic formula: x = (-b ± √(b² - 4ac)) / (2a)
- Completing the square: Rewrite in the form (x - h)² = k.

The discriminant (b² - 4ac) determines the nature of roots:
- Positive: Two distinct real roots
- Zero: One repeated real root
- Negative: Two complex conjugate roots

### Systems of Equations
A system of linear equations involves two or more equations with the same variables. Methods of solving:
- Substitution: Solve one equation for a variable and substitute into the other.
- Elimination: Add or subtract equations to eliminate a variable.
- Matrix methods: Use augmented matrices and row reduction.

### Polynomials
A polynomial is an expression consisting of variables and coefficients with non-negative integer exponents. Key operations include addition, subtraction, multiplication, and division (long division and synthetic division).

The Fundamental Theorem of Algebra states that every non-zero polynomial of degree n has exactly n complex roots (counting multiplicity).

### Inequalities
Inequalities compare expressions using <, >, ≤, ≥. Solving inequalities follows similar rules to equations, except multiplying or dividing by a negative number reverses the inequality sign.

Compound inequalities combine two inequalities: a < x < b means x is between a and b.
""",
        "calculus": """## Calculus

### Limits
A limit describes the value a function approaches as the input approaches a specific value. Notation: lim(x→a) f(x) = L means f(x) gets arbitrarily close to L as x approaches a.

Key limit laws: sum, product, quotient rules. L'Hôpital's Rule resolves indeterminate forms (0/0 or ∞/∞) by taking the ratio of derivatives.

### Derivatives
The derivative measures the instantaneous rate of change of a function. Definition: f'(x) = lim(h→0) [f(x+h) - f(x)] / h.

Key rules:
- Power rule: d/dx[xⁿ] = nxⁿ⁻¹
- Product rule: d/dx[f·g] = f'g + fg'
- Quotient rule: d/dx[f/g] = (f'g - fg') / g²
- Chain rule: d/dx[f(g(x))] = f'(g(x)) · g'(x)

Applications include finding maxima/minima, velocity/acceleration, and rates of change.

### Integrals
Integration is the reverse of differentiation. The indefinite integral ∫f(x)dx = F(x) + C where F'(x) = f(x).

The Fundamental Theorem of Calculus connects differentiation and integration:
∫[a,b] f(x)dx = F(b) - F(a)

Techniques: substitution, integration by parts (∫u dv = uv - ∫v du), partial fractions, trigonometric substitution.

### Applications of Integration
- Area between curves: ∫[a,b] [f(x) - g(x)] dx
- Volume of revolution: Disk method π∫[a,b] [f(x)]² dx, Shell method 2π∫[a,b] x·f(x) dx
- Arc length: ∫[a,b] √(1 + [f'(x)]²) dx
- Work: W = ∫[a,b] F(x) dx

### Series and Sequences
A sequence is an ordered list of numbers. A series is the sum of a sequence.
- Geometric series: Σ arⁿ converges if |r| < 1, sum = a/(1-r)
- Taylor series: f(x) = Σ f⁽ⁿ⁾(a)/n! · (x-a)ⁿ
- Convergence tests: Ratio test, root test, comparison test, integral test.
""",
    },
    "cs": {
        "data_structures": """## Data Structures

### Arrays
An array stores elements of the same type in contiguous memory. Access is O(1) by index. Insertion/deletion at arbitrary positions is O(n) due to shifting.

Dynamic arrays (like Python lists) automatically resize when capacity is reached, typically doubling in size. Amortized insertion is O(1).

### Linked Lists
A linked list stores elements in nodes, each containing data and a pointer to the next node. Types:
- Singly linked: Each node points to the next.
- Doubly linked: Each node points to both next and previous.
- Circular: The last node points back to the first.

Operations: Insert/delete at head O(1), search O(n), insert at position O(n).

### Stacks and Queues
Stack (LIFO): push O(1), pop O(1), peek O(1). Used for function calls, expression evaluation, backtracking.
Queue (FIFO): enqueue O(1), dequeue O(1). Used for BFS, scheduling, buffering.
Priority Queue: Elements have priorities; dequeue returns highest priority. Often implemented with a heap.

### Trees
A tree is a hierarchical structure with a root node and children.
- Binary Tree: Each node has at most 2 children.
- Binary Search Tree (BST): Left child < parent < right child. Search/insert/delete O(h) where h is height.
- Balanced BSTs (AVL, Red-Black): Maintain O(log n) height through rotations.
- Heap: Complete binary tree satisfying the heap property (min-heap or max-heap).

### Hash Tables
Hash tables map keys to values using a hash function. Average case: insert/search/delete O(1).
Collision resolution:
- Chaining: Each bucket holds a linked list.
- Open addressing: Linear probing, quadratic probing, double hashing.
Load factor = n/m where n is number of entries and m is number of buckets. Rehash when load factor exceeds a threshold.

### Graphs
A graph G = (V, E) consists of vertices and edges. Types: directed/undirected, weighted/unweighted.
Representations: Adjacency matrix O(V²) space, adjacency list O(V+E) space.
Traversals: BFS (queue, O(V+E)), DFS (stack/recursion, O(V+E)).
""",
        "algorithms": """## Algorithms

### Sorting Algorithms
- Bubble Sort: Compare adjacent elements, swap if needed. O(n²) average/worst.
- Selection Sort: Find minimum, place at front. O(n²).
- Insertion Sort: Build sorted array one element at a time. O(n²) worst, O(n) best.
- Merge Sort: Divide and conquer. O(n log n) guaranteed. Stable. O(n) extra space.
- Quick Sort: Partition around pivot. O(n log n) average, O(n²) worst. In-place.
- Heap Sort: Build a heap, extract max repeatedly. O(n log n). In-place, not stable.

### Searching Algorithms
- Linear Search: Check every element. O(n).
- Binary Search: Requires sorted array. Compare with middle, eliminate half. O(log n).
- Interpolation Search: Improved binary search for uniformly distributed data. O(log log n) average.

### Graph Algorithms
- Dijkstra's Algorithm: Shortest path from single source. O((V+E) log V) with min-heap. Non-negative weights only.
- Bellman-Ford: Shortest path with negative weights. O(VE). Detects negative cycles.
- Floyd-Warshall: All-pairs shortest paths. O(V³).
- Kruskal's Algorithm: Minimum spanning tree using edge sorting and union-find. O(E log E).
- Prim's Algorithm: MST by growing a tree from a vertex. O((V+E) log V).
- Topological Sort: Linear ordering of DAG vertices. O(V+E).

### Dynamic Programming
DP solves problems by breaking them into overlapping subproblems with optimal substructure.
Approaches: Top-down (memoization) and bottom-up (tabulation).

Classic problems:
- Fibonacci: F(n) = F(n-1) + F(n-2). O(n) with DP vs O(2ⁿ) naive.
- Knapsack: Maximize value with weight constraint. O(nW).
- Longest Common Subsequence: O(mn).
- Edit Distance: O(mn).

### Complexity Analysis
Big-O notation describes upper bound growth rate.
Common complexities: O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2ⁿ) < O(n!).
Space complexity measures additional memory used.
Amortized analysis considers average cost over a sequence of operations.
""",
    },
    "science": {
        "physics": """## Physics

### Mechanics
Newton's Laws of Motion:
1. An object at rest stays at rest; an object in motion stays in motion (unless acted upon by a net force).
2. F = ma. Force equals mass times acceleration.
3. For every action, there is an equal and opposite reaction.

Kinematics equations (constant acceleration):
- v = v₀ + at
- x = x₀ + v₀t + ½at²
- v² = v₀² + 2a(x - x₀)

Energy:
- Kinetic energy: KE = ½mv²
- Potential energy: PE = mgh (gravitational), PE = ½kx² (elastic)
- Conservation of energy: Total energy in a closed system is constant.
- Work: W = F·d·cos(θ)

Momentum: p = mv. Conservation of momentum in collisions.
- Elastic collision: Both momentum and kinetic energy are conserved.
- Inelastic collision: Momentum is conserved; kinetic energy is not.

### Thermodynamics
Laws of Thermodynamics:
0. If A is in thermal equilibrium with B, and B with C, then A is in equilibrium with C.
1. Energy conservation: ΔU = Q - W (internal energy change = heat added - work done).
2. Entropy of an isolated system never decreases. Heat flows from hot to cold.
3. As temperature approaches absolute zero, entropy approaches a minimum.

Heat transfer: Conduction (Q/t = kA·ΔT/L), convection, radiation (P = εσAT⁴).

### Electromagnetism
Coulomb's Law: F = kq₁q₂/r². Electric field E = F/q.
Gauss's Law: ∮E·dA = Q_enc/ε₀.
Ohm's Law: V = IR. Power: P = IV = I²R = V²/R.
Magnetic force: F = qv × B. Faraday's Law: EMF = -dΦ/dt.
Maxwell's equations unify electric and magnetic fields, predicting electromagnetic waves traveling at c ≈ 3×10⁸ m/s.

### Waves and Optics
Wave properties: wavelength (λ), frequency (f), speed (v = λf), amplitude.
Types: transverse (light), longitudinal (sound).
Interference: Constructive (waves in phase), destructive (waves out of phase).
Snell's Law: n₁sin(θ₁) = n₂sin(θ₂). Total internal reflection when angle exceeds critical angle.
""",
        "chemistry": """## Chemistry

### Atomic Structure
Atoms consist of protons, neutrons, and electrons. Atomic number = number of protons. Mass number = protons + neutrons.

Electron configuration follows: Aufbau principle (fill lowest energy first), Pauli exclusion principle (max 2 electrons per orbital), Hund's rule (fill orbitals singly before pairing).

Quantum numbers: n (principal), l (angular momentum), ml (magnetic), ms (spin).

### Chemical Bonding
Types of bonds:
- Ionic: Transfer of electrons between metals and non-metals. High melting points, conduct electricity when dissolved.
- Covalent: Sharing of electrons between non-metals. Polar (unequal sharing) and non-polar (equal sharing).
- Metallic: Sea of delocalized electrons. Explains conductivity, malleability, ductility.

VSEPR theory predicts molecular geometry based on electron pair repulsion.
Hybridization (sp, sp², sp³) explains bonding geometry.

### Chemical Reactions
Types: Synthesis (A + B → AB), decomposition (AB → A + B), single replacement, double replacement, combustion.

Balancing equations: Conserve atoms on both sides using coefficients.
Stoichiometry: Mole ratios from balanced equations to calculate reactant/product quantities.
Limiting reagent: The reactant that is consumed first, determining the maximum product yield.

### Thermochemistry
Enthalpy (H): Heat content at constant pressure. ΔH < 0 exothermic, ΔH > 0 endothermic.
Hess's Law: ΔH for a reaction is the same regardless of pathway.
Bond energies: ΔH ≈ Σ(bonds broken) - Σ(bonds formed).

### Equilibrium
Chemical equilibrium: Rate of forward reaction equals rate of reverse reaction.
Equilibrium constant: K = [products]/[reactants] (each raised to stoichiometric coefficients).
Le Chatelier's Principle: A system at equilibrium shifts to counteract changes in concentration, pressure, or temperature.

### Acids and Bases
Arrhenius: Acids produce H⁺, bases produce OH⁻.
Brønsted-Lowry: Acids donate protons, bases accept protons.
pH = -log[H⁺]. pOH = -log[OH⁻]. pH + pOH = 14.
Strong acids/bases dissociate completely. Weak acids/bases partially dissociate (Ka, Kb).
Buffer solutions resist pH changes: Composed of weak acid + conjugate base (or vice versa).
""",
    },
    "history": {
        "world_history": """## World History

### Ancient Civilizations
Mesopotamia (3500-500 BCE): Cradle of civilization between Tigris and Euphrates rivers. Sumerians invented cuneiform writing, the wheel, and established the first cities (Ur, Uruk). Hammurabi's Code was one of the earliest written legal codes.

Ancient Egypt (3100-30 BCE): Civilization along the Nile. Known for pyramids, hieroglyphics, mummification. Pharaohs were considered divine rulers. Key periods: Old Kingdom (pyramids), Middle Kingdom (expansion), New Kingdom (Tutankhamun, Ramesses II).

Ancient Greece (800-146 BCE): Birthplace of democracy (Athens), philosophy (Socrates, Plato, Aristotle), and the Olympic Games. Alexander the Great spread Hellenistic culture across the known world. Major contributions to mathematics, science, literature, and art.

Roman Empire (27 BCE-476 CE): Grew from a republic to a vast empire. Contributions include Roman law, architecture (Colosseum, aqueducts), roads, and Latin language. Fall of Western Rome in 476 CE marked the end of the ancient period.

### Medieval Period (500-1500 CE)
Feudal system organized society into lords, vassals, and serfs. The Catholic Church was the dominant institution in medieval Europe.

The Crusades (1096-1291): Military campaigns to reclaim the Holy Land. Led to increased trade and cultural exchange between Europe and the Middle East.

The Black Death (1347-1351): Bubonic plague killed approximately one-third of Europe's population, leading to labor shortages, social upheaval, and eventually contributing to the end of feudalism.

### Renaissance and Reformation (1400-1600)
The Renaissance ("rebirth") began in Italy. Revival of classical learning, humanism, art (Leonardo da Vinci, Michelangelo), and science. The printing press (Gutenberg, 1440) revolutionized information spread.

The Protestant Reformation (1517): Martin Luther's 95 Theses challenged Catholic practices. Led to the formation of Protestant denominations and the Counter-Reformation.

### Age of Revolutions (1700-1900)
The Enlightenment emphasized reason, individual rights, and scientific inquiry. Key thinkers: Locke, Voltaire, Rousseau, Montesquieu.

American Revolution (1775-1783): Colonies declared independence from Britain. The Constitution established a federal republic with separation of powers.

French Revolution (1789-1799): Overthrew the monarchy, established republican ideals. The Declaration of the Rights of Man proclaimed liberty, equality, fraternity.

Industrial Revolution (1760-1840): Shift from agrarian to industrial economies. Steam engine, factories, urbanization. Transformed labor, transportation, and social structures.
""",
    },
}


def generate_curriculum_files():
    """Write all curriculum data to text files organized by subject/topic."""
    print("=" * 60)
    print("Generating Sample Curriculum Files")
    print("=" * 60)

    for subject, topics in CURRICULA.items():
        subject_dir = os.path.join(CURRICULA_DIR, subject)
        os.makedirs(subject_dir, exist_ok=True)

        for topic, content in topics.items():
            filepath = os.path.join(subject_dir, f"{topic}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"  Created: {filepath}")

    print(f"\nGenerated curriculum files in {CURRICULA_DIR}/")
    print("Subjects:", ", ".join(CURRICULA.keys()))


if __name__ == "__main__":
    generate_curriculum_files()
