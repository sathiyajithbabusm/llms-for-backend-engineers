import json, sys
cells = []
def md(s): cells.append({"cell_type":"markdown","metadata":{},"source":s.strip("\n")})
def code(s): cells.append({"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s.strip("\n")})

md("""
# Attention Is Just a Fuzzy Database Lookup — runnable companion

Companion notebook for **LLMs for Backend Engineers — Part 1**. Run each cell, then change the numbers and see what happens.
""")
code("""
import numpy as np
np.set_printoptions(precision=2, suppress=True)
""")
md("## 1. The exact lookup you already know")
code("""
capitals = {"france": "Paris", "japan": "Tokyo", "india": "New Delhi"}
print(capitals["japan"])
try:
    capitals["japn"]
except KeyError as e:
    print("KeyError:", e)
""")
md("## 2. Attention: a soft lookup")
code("""
def softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))  # subtract max for numerical stability
    return e / e.sum(axis=-1, keepdims=True)

def attention(Q, K, V, mask=None):
    d_k = K.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)       # how well each query matches each key
    if mask is not None:
        scores = np.where(mask, scores, -np.inf)
    weights = softmax(scores)              # each row now sums to 1
    return weights @ V, weights            # weighted blend of the values
""")
md("""
### The support-ticket example
*"The customer returned the order because **it** arrived damaged."*

Dimensions: `[can_be_shipped, is_a_person, is_an_action]`
""")
code("""
K = np.array([[4.0, 0.0, 0.0],   # order
              [0.0, 4.0, 0.0],   # customer
              [0.0, 0.0, 4.0]])  # returned

V = np.array([[1.0, 0.0],        # what "order" contributes
              [0.0, 1.0],        # what "customer" contributes
              [0.5, 0.5]])       # what "returned" contributes

q = np.array([[1.0, 0.0, 0.2]])  # "it"

output, weights = attention(q, K, V)
for name, w in zip(["order", "customer", "returned"], weights[0]):
    print(f"{name:>9}: {w:.0%}")
print("output:", output)
""")
md("""
**Try it:** change the query to `[0.0, 1.0, 0.0]` (looking for a person) and watch the weight move to "customer".
""")
md("## 3. Why we divide by √d — without scaling, the lookup stops being fuzzy")
code("""
# Real models use hundreds of dimensions, so raw dot products get large.
rng = np.random.default_rng(42)
d = 512
q_big = rng.normal(size=(1, d))
K_big = rng.normal(size=(5, d))

print("unscaled:", softmax(q_big @ K_big.T))               # collapses toward one row
print("scaled:  ", softmax(q_big @ K_big.T / np.sqrt(d)))  # stays a real blend
""")
md("## 4. Self-attention: Q, K and V all come from the same sentence (a self-join)")
code("""
tokens = ["The", "customer", "returned", "the", "order", "because", "it", "arrived", "damaged"]
rng = np.random.default_rng(0)
d_model, d_head = 16, 8
X = rng.normal(size=(len(tokens), d_model))          # one vector per token
W_q, W_k, W_v = (rng.normal(size=(d_model, d_head)) / np.sqrt(d_model) for _ in range(3))  # learned in a real model

out, w = attention(X @ W_q, X @ W_k, X @ W_v)
print(out.shape, "-> one blended vector per token")
print("rows sum to:", w.sum(axis=1))
""")
md("""
## 5. The causal mask: `WHERE b.position <= a.position`
A text-generating model can't look at future tokens.
""")
code("""
n = len(tokens)
causal = np.tril(np.ones((n, n), dtype=bool))
out, w = attention(X @ W_q, X @ W_k, X @ W_v, mask=causal)
print(w)   # upper triangle is all zeros
""")
md("""
## 6. Multi-head attention: several indexes on the same table
Random weights here, so the patterns are meaningless — in a trained model each head learns its own pattern.
""")
code("""
def multi_head(X, n_heads=4, d_head=4, seed=1):
    rng = np.random.default_rng(seed)
    outs = []
    for _ in range(n_heads):
        W_q, W_k, W_v = (rng.normal(size=(X.shape[1], d_head)) / np.sqrt(X.shape[1]) for _ in range(3))
        o, _ = attention(X @ W_q, X @ W_k, X @ W_v, mask=causal)
        outs.append(o)
    W_o = rng.normal(size=(n_heads * d_head, X.shape[1]))
    return np.concatenate(outs, axis=-1) @ W_o   # concatenate heads, mix back together

print(multi_head(X).shape)
""")
md("## 7. The catch: it's a cross join — O(n²)")
code("""
for n_tok in [1_000, 8_000, 32_000, 128_000, 1_000_000]:
    print(f"{n_tok:>9,} tokens -> {n_tok**2:>22,} scores per head, per layer")
""")
md("""
---
Next in the series: **The KV Cache Is Just Memoization — and It's Why Your Long Prompts Cost More.**
""")
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
      "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
for i, c in enumerate(nb["cells"]): c["id"] = f"cell-{i}"
json.dump(nb, open(sys.argv[1], "w"), indent=1)
open(sys.argv[2], "w").write("\n\n".join(c["source"] for c in cells if c["cell_type"] == "code"))
