import cloudApi from '../lib/cloud-api.js';
export async function onRequest(context) {
  const gate = await cloudApi.handleGate(context.request, { token: context.env.VIEWER_TOKEN });
  if (gate instanceof Response) return gate;          // 404
  const res = await context.next();
  if (gate && gate.setCookie) {
    const out = new Response(res.body, res);
    return cloudApi.applyGateCookie(out, gate.setCookie);
  }
  return res;
}
