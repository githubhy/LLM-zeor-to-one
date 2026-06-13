# Attention Mechanisms — Demo Survey

<a id="p-attention-mechanisms-demo-survey-1"></a><!-- para:attention-mechanisms-demo-survey-1 --> This tiny survey exists to smoke-test the cross-link and math gates on LLM-domain content.

### 1 Scaled Dot-Product Attention

<a id="p-1-scaled-dot-product-attention-1"></a><!-- para:1-scaled-dot-product-attention-1 --> The core operation of the transformer is scaled dot-product attention. The output is defined by Equation <!-- ref:1-1 -->[(1)](#eq-1), which mixes value vectors weighted by query–key similarity.

<a id="eq-1"></a><!-- eq:1-1 -->
$$
\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V \tag{1}
$$

<a id="p-1-scaled-dot-product-attention-2"></a><!-- para:1-scaled-dot-product-attention-2 --> The scaling factor $1/\sqrt{d_k}$ keeps the softmax in a low-variance regime, as introduced by <!-- cite:1 --> [[1]](references.md#ref-1).

### 2 Efficient Attention Variants

<a id="p-2-efficient-attention-variants-1"></a><!-- para:2-efficient-attention-variants-1 --> Building on §1, memory-efficient kernels such as FlashAttention <!-- cite:2 --> [[2]](references.md#ref-2) compute the same softmax without materializing the full $n \times n$ attention matrix, trading recomputation for a smaller memory footprint.
