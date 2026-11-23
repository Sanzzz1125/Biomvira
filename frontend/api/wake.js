// Called by the two daily Vercel cron jobs in vercel.json (4:30-5:29 AM and 5:30-6:29 AM India time) to wake the free
// Render server before 6 AM; from then on the server keeps itself awake until midnight (backend/app/keep_awake.py).
// The very first request already starts Render's wake-up; the retries only wait until the server answers.
const HEALTH_URL = 'https://biomvira-api.onrender.com/api/health';
const WAIT_MS = 50_000;

export async function GET(request) {
  const secret = process.env.CRON_SECRET;
  if (secret && request.headers.get('authorization') !== `Bearer ${secret}`) {
    return new Response('Unauthorized', { status: 401 });
  }
  const deadline = Date.now() + WAIT_MS;
  let last = 'no answer';
  while (Date.now() < deadline) {
    try {
      const response = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(Math.max(1_000, deadline - Date.now())) });
      if (response.ok) return Response.json({ awake: true });
      last = `HTTP ${response.status}`;
    } catch (error) {
      last = error.name;
    }
    await new Promise((resolve) => setTimeout(resolve, 5_000));
  }
  return Response.json({ awake: false, last }, { status: 504 });
}
