import cloudApi from '../../lib/cloud-api.js';
export const onRequestGet = (ctx) => cloudApi.handleManifest(ctx.request, { kv: ctx.env.ANNOTATIONS, token: ctx.env.VIEWER_TOKEN });
