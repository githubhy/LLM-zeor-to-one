## A Transformer Top-to-Neuron: a Fully Worked Toy Model

<a id="p-a-transformer-top-to-neuron-a-fully-worked-toy-model-1"></a><!-- para:a-transformer-top-to-neuron-a-fully-worked-toy-model-1 --> This appendix is the calibration chapter of the anatomy series. It builds the smallest model that still has every part of a real decoder LLM — embedding, a pre-norm block with a self-attention sublayer and a feed-forward sublayer, a final norm, and an unembedding — and derives its **complete forward pass, its complete backward pass with no step skipped, and one step of the Adam optimizer**, from first principles. The model is deliberately tiny ($V=3$, $d=4$, $T=3$, one head, $d_{ff}=8$, one block) so that every object is a small matrix you could check by hand. The derivations are validated against a finite-difference gradient check (the analytic gradients match to a maximum relative error of $1.6\times 10^{-9}$), so the math here is not merely asserted — it is verified. The attention *internals* (the QK and OV circuits, the $1/\sqrt{d_k}$ scaling, the softmax Jacobian) were dissected in Appendix A; this chapter wires them into the whole model and supplies everything else. The same anatomy, instantiated at scale, is the subject of the chapters that follow.

<a id="p-a-transformer-top-to-neuron-a-fully-worked-toy-model-2"></a><!-- para:a-transformer-top-to-neuron-a-fully-worked-toy-model-2 --> Notation follows Appendix A: vectors are **bold lowercase columns**, matrices are non-bold capitals, scalars non-bold lowercase. We write the per-position hidden vectors as the rows of a matrix $H \in \mathbb{R}^{T\times d}$ for compactness.

<!-- sec:C.1 -->
### <a id="sec-C.1"></a>C.1 The Model and the Residual Stream

<a id="p-c1-the-model-and-the-residual-stream-1"></a><!-- para:c1-the-model-and-the-residual-stream-1 --> The toy model maps a length-$T$ token sequence to a next-token distribution at each position. Its computation is a straight climb up a **residual stream** — a running $d$-dimensional vector per position that each sublayer *reads from* and *adds to* — from the embedding at the bottom to the logits at the top.

<a id="p-c1-the-model-and-the-residual-stream-2"></a><!-- para:c1-the-model-and-the-residual-stream-2 --> ![Three-panel zoom: the whole model as a bottom-to-top stack (input tokens, embedding, decoder block, final LayerNorm, unembedding, softmax/loss); one decoder block (LayerNorm, self-attention, residual add, LayerNorm, FFN, residual add); and the FFN drawn as input units, eight ReLU hidden units with one highlighted, and output units, showing a single neuron as one column of the first weight matrix feeding a ReLU feeding one row of the second weight matrix.](figures/appendix-c-anatomy.svg)

<!-- sec:C.1-figure-c -->
<a id="p-c1-the-model-and-the-residual-stream-3"></a><!-- para:c1-the-model-and-the-residual-stream-3 --> <a id="sec-C.1-figure-c"></a>**Figure C.1.** The toy model from the top structure down to a single neuron. *Left:* the whole model — token ids to embedding to one decoder block ($\times L$) to final LayerNorm to unembedding to softmax/loss. *Middle:* one decoder block — a pre-norm self-attention sublayer and a pre-norm feed-forward sublayer, each wrapped in a residual add (the dashed skip lines); the head internals are dissected in <!-- secxref:A.2 -->[§A.2](appendix-a-qkv-first-principles.md#sec-A.2). *Right:* the feed-forward network down to one neuron $k$ — its incoming weights are one column of $W_1$, its outgoing weights one row of $W_2$. Config: $V=3$, $d=4$, $T=3$, $d_{ff}=8$. Regenerate via `surveys/llms-for-coding/figures/appendix-c-anatomy.py`.

<a id="p-c1-the-model-and-the-residual-stream-4"></a><!-- para:c1-the-model-and-the-residual-stream-4 --> The parameters are an inventory of small tensors: token and position embeddings $E\in\mathbb{R}^{V\times d}$ and $P\in\mathbb{R}^{T\times d}$; the head's projections $W_Q, W_K, W_V\in\mathbb{R}^{d\times d_k}$ and $W_O\in\mathbb{R}^{d_k\times d}$; two LayerNorm gain/bias pairs $(\boldsymbol{\gamma}^1,\boldsymbol{\beta}^1)$ and $(\boldsymbol{\gamma}^2,\boldsymbol{\beta}^2)$ inside the block plus a final pair $(\boldsymbol{\gamma}^F,\boldsymbol{\beta}^F)$; the feed-forward weights $W_1\in\mathbb{R}^{d\times d_{ff}}$, $\mathbf{b}_1\in\mathbb{R}^{d_{ff}}$, $W_2\in\mathbb{R}^{d_{ff}\times d}$, $\mathbf{b}_2\in\mathbb{R}^{d}$; and the unembedding $W_U\in\mathbb{R}^{d\times V}$, $\mathbf{b}_U\in\mathbb{R}^{V}$. At the toy dimensions this is $203$ scalars in total. We train on one fixed sequence $x=(0,1,2)$ with next-token targets $y=(1,2,0)$ — predicting the next symbol of a $3$-cycle — under the causal cross-entropy loss of Section <!-- secxref:3.1 -->[§3.1](language-models-from-first-principles.md#sec-3.1).

<!-- sec:C.2 -->
### <a id="sec-C.2"></a>C.2 The Forward Pass

<a id="p-c2-the-forward-pass-1"></a><!-- para:c2-the-forward-pass-1 --> **Embedding.** Each position's stream is seeded by adding the token embedding to a learned positional embedding:

<a id="eq-1"></a><!-- eq:C-1 -->
$$
\mathbf{h}^0_t = E[x_t] + P_t, \qquad t = 1,\dots,T. \tag{1}
$$

<a id="p-c2-the-forward-pass-2"></a><!-- para:c2-the-forward-pass-2 --> **LayerNorm.** Both sublayers are *pre-norm*: they read a normalized copy of the stream. For a row vector $\mathbf{h}\in\mathbb{R}^d$ with mean $\mu$ and variance $\sigma^2$ over its $d$ entries,

<a id="eq-2"></a><!-- eq:C-2 -->
$$
\mathrm{LN}(\mathbf{h}) = \boldsymbol{\gamma}\odot\hat{\mathbf{h}} + \boldsymbol{\beta},
\qquad \hat{\mathbf{h}} = \frac{\mathbf{h}-\mu}{\sqrt{\sigma^2+\varepsilon}},
\qquad \mu = \tfrac{1}{d}\textstyle\sum_i h_i, \ \ \sigma^2 = \tfrac{1}{d}\textstyle\sum_i (h_i-\mu)^2. \tag{2}
$$

<a id="p-c2-the-forward-pass-3"></a><!-- para:c2-the-forward-pass-3 --> **Attention sublayer.** Read the normalized stream $A^1 = \mathrm{LN}(H^0)$, form queries/keys/values, score and causally soft-combine the values (the mechanism of Appendix A), project, and add back:

<a id="eq-3"></a><!-- eq:C-3 -->
$$
\begin{aligned}
Q = A^1 W_Q,\quad K = A^1 W_K,&\quad V = A^1 W_V
&&\text{(per-position projections)}\\
S = \tfrac{1}{\sqrt{d_k}}\,Q K^{\top},\quad A_{\!w} &= \mathrm{softmax}_{\text{causal}}(S)
&&\text{(scores, causal softmax; A.7)}\\
H^1 &= H^0 + (A_{\!w} V)\,W_O
&&\text{(context, output projection, residual add)}
\end{aligned} \tag{3}
$$

<a id="p-c2-the-forward-pass-4"></a><!-- para:c2-the-forward-pass-4 --> **Feed-forward sublayer, down to one neuron.** Read $A^2 = \mathrm{LN}(H^1)$, pass it through a one-hidden-layer MLP with a ReLU, and add back:

<a id="eq-4"></a><!-- eq:C-4 -->
$$
\begin{aligned}
Z = A^2 W_1 + \mathbf{b}_1^{\top}, \quad G &= \mathrm{ReLU}(Z)
&&\text{(}d_{ff}\text{ hidden pre-activations, then the nonlinearity)}\\
H^2 &= H^1 + G W_2 + \mathbf{b}_2^{\top}
&&\text{(write the FFN output to the stream)}
\end{aligned} \tag{4}
$$

<a id="p-c2-the-forward-pass-5"></a><!-- para:c2-the-forward-pass-5 --> A single hidden unit — *one neuron* $k$ — reads the stream through one column of $W_1$ and writes through one row of $W_2$: with $g_k = \mathrm{ReLU}(W_1[:,k]^{\top}\mathbf{a}^2 + b_{1,k})$ its contribution to the output is $g_k\, W_2[k,:]$. The neuron is a **matched filter on the residual stream**: $W_1[:,k]$ is the feature it detects, the ReLU gates it on only when that feature is present, and $W_2[k,:]$ is what it then adds back — a key-to-value memory write, the picture of <!-- secxref:A.6 -->[§A.6](appendix-a-qkv-first-principles.md#sec-A.6) applied to the MLP rather than to attention.

<a id="p-c2-the-forward-pass-6"></a><!-- para:c2-the-forward-pass-6 --> **Output.** Normalize once more, unembed to vocabulary logits, and take the causal cross-entropy against the targets:

<a id="eq-5"></a><!-- eq:C-5 -->
$$
\begin{aligned}
H^F = \mathrm{LN}(H^2),\quad &\mathrm{logits} = H^F W_U + \mathbf{b}_U^{\top}
&&\text{(final norm, unembedding)}\\
\mathbf{p}_t = \mathrm{softmax}(\mathrm{logits}_t),\quad &\mathcal{L} = -\tfrac{1}{T}\textstyle\sum_{t=1}^{T}\log p_{t,\,y_t}
&&\text{(per-position softmax, mean NLL)}
\end{aligned} \tag{5}
$$

> <a id="p-c2-the-forward-pass-7"></a><!-- para:c2-the-forward-pass-7 --> **Note — the residual stream is a bus, not a pipe.** Every sublayer in Equations <!-- ref:C-3 -->[(3)](#eq-3) and <!-- ref:C-4 -->[(4)](#eq-4) has the shape $H \leftarrow H + (\text{read from } \mathrm{LN}(H))$: it adds a correction rather than replacing the stream. That additive structure is exactly what makes the backward pass below a sum of clean, local contributions, and what lets gradients reach the embedding undiminished.

<!-- sec:C.3 -->
### <a id="sec-C.3"></a>C.3 The Backward Pass, With No Step Missing

<a id="p-c3-the-backward-pass-with-no-step-missing-1"></a><!-- para:c3-the-backward-pass-with-no-step-missing-1 --> Training needs $\partial\mathcal{L}/\partial\theta$ for every parameter. Backprop is the chain rule run once from the loss down the same graph, carrying the gradient $\mathrm{d}U \equiv \partial\mathcal{L}/\partial U$ of each intermediate $U$. We take the modules in reverse order of Equations <!-- ref:C-1 -->[(1)](#eq-1)–<!-- ref:C-5 -->[(5)](#eq-5).

<a id="p-c3-the-backward-pass-with-no-step-missing-2"></a><!-- para:c3-the-backward-pass-with-no-step-missing-2 --> **Softmax + cross-entropy.** The loss reaches the logits only through the softmax. Differentiating $-\log p_{t,y_t}$ with $p_{t,j}=e^{\ell_{t,j}}/\sum_k e^{\ell_{t,k}}$ collapses to the standard result:

<a id="eq-6"></a><!-- eq:C-6 -->
$$
\begin{aligned}
\frac{\partial\mathcal{L}}{\partial \ell_{t,j}}
&= \tfrac{1}{T}\,\frac{\partial(-\log p_{t,y_t})}{\partial \ell_{t,j}}
&&\text{(mean over }T\text{ positions)}\\
&= \tfrac{1}{T}\,(p_{t,j} - \mathbb{1}[\,j=y_t\,])
&&\text{(softmax Jacobian A.11, then the log derivative)}
\end{aligned} \tag{6}
$$

<a id="p-c3-the-backward-pass-with-no-step-missing-3"></a><!-- para:c3-the-backward-pass-with-no-step-missing-3 --> so $\mathrm{d}\,\mathrm{logits} = (P_{\!r} - Y)/T$ with $Y$ the one-hot target matrix — the predicted-minus-true signal, the single cleanest gradient in the whole network.

<a id="p-c3-the-backward-pass-with-no-step-missing-4"></a><!-- para:c3-the-backward-pass-with-no-step-missing-4 --> **Unembedding.** With $\mathrm{logits} = H^F W_U + \mathbf{b}_U^{\top}$, the matrix-product rule gives $\mathrm{d}W_U = (H^F)^{\top}\,\mathrm{d}\,\mathrm{logits}$, $\mathrm{d}\mathbf{b}_U = \sum_t \mathrm{d}\,\mathrm{logits}_t$, and $\mathrm{d}H^F = \mathrm{d}\,\mathrm{logits}\,W_U^{\top}$.

<a id="p-c3-the-backward-pass-with-no-step-missing-5"></a><!-- para:c3-the-backward-pass-with-no-step-missing-5 --> **LayerNorm.** Each norm needs the gradient through Equation <!-- ref:C-2 -->[(2)](#eq-2). Writing $n=d$ and $\mathbf{u} = \mathrm{d}Y\odot\boldsymbol{\gamma}$ for the incoming gradient pulled through the gain, the per-row result is

<a id="eq-7"></a><!-- eq:C-7 -->
$$
\begin{aligned}
\mathrm{d}\boldsymbol{\gamma} = \textstyle\sum_t \mathrm{d}Y_t\odot\hat{\mathbf{h}}_t,\quad
&\mathrm{d}\boldsymbol{\beta} = \textstyle\sum_t \mathrm{d}Y_t
&&\text{(affine parameters)}\\
\mathrm{d}\mathbf{h} = \tfrac{1}{\sqrt{\sigma^2+\varepsilon}}\big(\mathbf{u} - \tfrac{1}{n}\textstyle\sum_i u_i - \hat{\mathbf{h}}\,\tfrac{1}{n}\textstyle\sum_i u_i \hat{h}_i\big)
&&\text{(subtract the mean- and variance-direction projections)}
\end{aligned} \tag{7}
$$

<a id="p-c3-the-backward-pass-with-no-step-missing-6"></a><!-- para:c3-the-backward-pass-with-no-step-missing-6 --> The two subtractions are the gradient's memory that LayerNorm removed a mean and a scale: a normalized layer is *blind* to shifts and rescalings of its input, so it passes no gradient along those two directions.

<a id="p-c3-the-backward-pass-with-no-step-missing-7"></a><!-- para:c3-the-backward-pass-with-no-step-missing-7 --> **Feed-forward backward (and one neuron's gradient).** The residual add in Equation <!-- ref:C-4 -->[(4)](#eq-4) routes $\mathrm{d}H^2$ both straight to $\mathrm{d}H^1$ and into the FFN. Through the FFN:

<a id="eq-8"></a><!-- eq:C-8 -->
$$
\begin{aligned}
\mathrm{d}W_2 = G^{\top}\,\mathrm{d}H^2,\quad \mathrm{d}\mathbf{b}_2 = \textstyle\sum_t \mathrm{d}H^2_t,\quad
&\mathrm{d}G = \mathrm{d}H^2\, W_2^{\top}
&&\text{(second linear)}\\
\mathrm{d}Z = \mathrm{d}G \odot \mathbb{1}[\,Z>0\,],\qquad
&\mathrm{d}W_1 = (A^2)^{\top}\,\mathrm{d}Z
&&\text{(ReLU gate, then first linear)}
\end{aligned} \tag{8}
$$

<a id="p-c3-the-backward-pass-with-no-step-missing-8"></a><!-- para:c3-the-backward-pass-with-no-step-missing-8 --> with $\mathrm{d}\mathbf{b}_1 = \sum_t \mathrm{d}Z_t$ and the sublayer's stream gradient $\mathrm{d}A^2 = \mathrm{d}Z\,W_1^{\top}$ flowing back through LayerNorm 2 by Equation <!-- ref:C-7 -->[(7)](#eq-7) and adding into $\mathrm{d}H^1$. For one neuron $k$ the relevant slices are $\mathrm{d}W_1[:,k]=\sum_t a^2_t\,\mathrm{d}z_{t,k}$ and $\mathrm{d}W_2[k,:]=\sum_t g_{t,k}\,\mathrm{d}h^2_t$ — the neuron learns only from positions where the ReLU let it fire ($z_{t,k}>0$).

<a id="p-c3-the-backward-pass-with-no-step-missing-9"></a><!-- para:c3-the-backward-pass-with-no-step-missing-9 --> **Attention backward.** The residual add in Equation <!-- ref:C-3 -->[(3)](#eq-3) again splits $\mathrm{d}H^1$ to $\mathrm{d}H^0$ and into the head. Pulling back through the output projection, the value-mix, the causal softmax, and the score-scaling reuses the head Jacobians of Appendix A — the softmax-row Jacobian of <!-- secxref:A.11 -->[§A.11](appendix-a-qkv-first-principles.md#sec-A.11):

<a id="eq-9"></a><!-- eq:C-9 -->
$$
\begin{aligned}
\mathrm{d}W_O = (A_{\!w} V)^{\top}\mathrm{d}R,\quad
\mathrm{d}V = A_{\!w}^{\top}(\mathrm{d}R\,W_O^{\top}),\quad
&\mathrm{d}A_{\!w} = (\mathrm{d}R\,W_O^{\top})\,V^{\top}
&&\text{(output proj }R\text{, value-mix)}\\
\mathrm{d}S_{t,:} = \tfrac{1}{\sqrt{d_k}}\,A_{\!w,t}\odot\big(\mathrm{d}A_{\!w,t} - (\mathrm{d}A_{\!w,t}\!\cdot\! A_{\!w,t})\big),\quad
&\mathrm{d}Q = \mathrm{d}S\,K,\ \ \mathrm{d}K = \mathrm{d}S^{\top}Q
&&\text{(softmax row-Jacobian A.11, scores)}
\end{aligned} \tag{9}
$$

<a id="p-c3-the-backward-pass-with-no-step-missing-10"></a><!-- para:c3-the-backward-pass-with-no-step-missing-10 --> with $\mathrm{d}W_Q = (A^1)^{\top}\mathrm{d}Q$, $\mathrm{d}W_K=(A^1)^{\top}\mathrm{d}K$, $\mathrm{d}W_V=(A^1)^{\top}\mathrm{d}V$, and $\mathrm{d}A^1 = \mathrm{d}Q\,W_Q^{\top} + \mathrm{d}K\,W_K^{\top} + \mathrm{d}V\,W_V^{\top}$ flowing back through LayerNorm 1 and adding into $\mathrm{d}H^0$ (here $R$ denotes the attention output before the residual add).

<a id="p-c3-the-backward-pass-with-no-step-missing-11"></a><!-- para:c3-the-backward-pass-with-no-step-missing-11 --> **Embedding.** The bottom of the stream: $\mathrm{d}P = \mathrm{d}H^0$ row-wise, and the token table accumulates the gradient at each used row, $\mathrm{d}E[v] = \sum_{t:\,x_t=v}\mathrm{d}H^0_t$ (a scatter-add — a token seen twice gets both contributions). That closes the pass: every parameter now has its gradient, and no link in Equations <!-- ref:C-1 -->[(1)](#eq-1)–<!-- ref:C-5 -->[(5)](#eq-5) was skipped.

<!-- sec:C.4 -->
### <a id="sec-C.4"></a>C.4 One Step of Adam

<a id="p-c4-one-step-of-adam-1"></a><!-- para:c4-one-step-of-adam-1 --> Gradient descent would update $\theta \leftarrow \theta - \eta\,\mathrm{d}\theta$. Adam instead keeps exponential moving averages of the gradient ($\mathbf{m}$) and its square ($\mathbf{v}$), bias-corrects them for their zero initialization, and takes a per-coordinate step normalized by the second moment. At step $\tau$, for every parameter coordinate:

<a id="eq-10"></a><!-- eq:C-10 -->
$$
\begin{aligned}
\mathbf{m} \leftarrow \beta_1\mathbf{m} + (1-\beta_1)\,\mathrm{d}\theta,\qquad
&\mathbf{v} \leftarrow \beta_2\mathbf{v} + (1-\beta_2)\,\mathrm{d}\theta^{2}
&&\text{(first/second moment EMAs)}\\
\hat{\mathbf{m}} = \frac{\mathbf{m}}{1-\beta_1^{\tau}},\quad
\hat{\mathbf{v}} = \frac{\mathbf{v}}{1-\beta_2^{\tau}},\qquad
&\theta \leftarrow \theta - \eta\,\frac{\hat{\mathbf{m}}}{\sqrt{\hat{\mathbf{v}}}+\epsilon}
&&\text{(bias correction, normalized step)}
\end{aligned} \tag{10}
$$

<a id="p-c4-one-step-of-adam-2"></a><!-- para:c4-one-step-of-adam-2 --> The normalization makes the step roughly scale-free: the very first update has magnitude $\approx\eta$ regardless of the gradient's size (because $\hat{\mathbf{m}}/\sqrt{\hat{\mathbf{v}}}\approx\mathrm{sign}(\mathrm{d}\theta)$ when $\mathbf{m},\mathbf{v}$ start at zero), which is why a learning rate around $10^{-2}$ behaves sensibly across the network's wildly different gradient scales.

<!-- sec:C.5 -->
### <a id="sec-C.5"></a>C.5 Validation, and the Toy Actually Learns

<a id="p-c5-validation-and-the-toy-actually-learns-1"></a><!-- para:c5-validation-and-the-toy-actually-learns-1 --> The derivations above are not asserted — they are checked. Implementing Equations <!-- ref:C-1 -->[(1)](#eq-1)–<!-- ref:C-10 -->[(10)](#eq-10) exactly and comparing the analytic gradient of every one of the $203$ parameters against a central finite difference gives a maximum relative error of $1.6\times 10^{-9}$ — machine agreement, so the forward and backward are mutually consistent and correct.

<a id="p-c5-validation-and-the-toy-actually-learns-2"></a><!-- para:c5-validation-and-the-toy-actually-learns-2 --> ![Two panels. Left: a scatter of analytic backprop gradients against numerical central-difference gradients for all 203 parameters, all lying on the line y equals x, with a maximum relative error around 1.6e-9. Right: the cross-entropy loss over 60 Adam steps at learning rate 0.02, falling from about 1.06 nats to near zero as the toy model learns the 3-cycle, with the uniform-guess baseline of natural-log 3 marked.](figures/appendix-c-gradcheck.svg)

<!-- sec:C.5-figure-c -->
<a id="p-c5-validation-and-the-toy-actually-learns-3"></a><!-- para:c5-validation-and-the-toy-actually-learns-3 --> <a id="sec-C.5-figure-c"></a>**Figure C.2.** The toy model, validated and trained. *Left:* every analytic parameter gradient (backprop, Equations <!-- ref:C-6 -->[(6)](#eq-6)–<!-- ref:C-9 -->[(9)](#eq-9)) matches a central finite difference to a maximum relative error of $1.6\times 10^{-9}$ — all $203$ points lie on $y=x$, so the backward pass is correct. *Right:* training with Adam (Equation <!-- ref:C-10 -->[(10)](#eq-10), learning rate $0.02$). One step lowers the loss from $1.06$ to $0.78$ nats; $60$ steps drive it to $\approx 5.6\times 10^{-3}$, far below the uniform-guess floor $\ln V = 1.10$ — the model has learned to predict the $3$-cycle. Deterministic; numbers in the `.json` sidecar. Regenerate via `surveys/llms-for-coding/figures/appendix-c-toy-transformer.py`.

<!-- sec:C.6 -->
### <a id="sec-C.6"></a>C.6 The Template for the Rest of the Series

<a id="p-c6-the-template-for-the-rest-of-the-series-1"></a><!-- para:c6-the-template-for-the-rest-of-the-series-1 --> Everything a frontier LLM does is in Figure C.1 and Equations <!-- ref:C-1 -->[(1)](#eq-1)–<!-- ref:C-10 -->[(10)](#eq-10); the larger models keep this skeleton and turn dials. The chapters that follow climb the size ladder and, at each rung, fully derive only what *changed* relative to this toy — leaving the invariant pieces (the residual stream, the softmax-plus-cross-entropy gradient, the LayerNorm backward, the Adam step) established here and cross-linked. What changes is concrete: the widths $d$, $d_{ff}$, the depth $L$, and the head count grow (Appendix D onward); the post-norm and learned-position choices of GPT-2 give way to pre-norm RMSNorm, rotary positions, and gated MLPs (Appendix E); keys and values are shared across heads (GQA/MQA); and the single dense MLP is replaced by a routed mixture of experts (Appendix G). The neuron of Figure C.1 — a gated read-then-write on the residual stream — is the unit that all of it is built from.
