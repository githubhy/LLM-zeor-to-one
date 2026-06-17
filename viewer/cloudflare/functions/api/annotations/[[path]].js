import cloudApi from '../../../lib/cloud-api.js';
const fileOf = (ctx) => (Array.isArray(ctx.params.path) ? ctx.params.path.join('/') : ctx.params.path);
const env = (ctx) => ({ kv: ctx.env.ANNOTATIONS, token: ctx.env.VIEWER_TOKEN });
export const onRequestGet = (ctx) => cloudApi.handleGetAnnotation(ctx.request, env(ctx), fileOf(ctx));
export const onRequestPut = (ctx) => cloudApi.handlePutAnnotation(ctx.request, env(ctx), fileOf(ctx));
