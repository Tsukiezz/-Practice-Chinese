# Facebook Login configuration

The Google and Facebook buttons are displayed side by side. Facebook remains
unavailable until a Meta application is configured; Google/email remain usable.
No credentials are included in this repository.

1. Create a Meta application with the Facebook Login use case for a website.
2. Configure the production website/origin as
   `https://hanzigo-chinese-learning.vercel.app` and its domain as
   `hanzigo-chinese-learning.vercel.app`. Enable the JavaScript SDK login flow
   and allow this origin in the Facebook Login settings shown by Meta.
3. Configure privacy policy and data deletion information required by Meta.
   Complete Meta's requirements for public access. In development mode, test
   only with accounts assigned an application role.
4. Add these **server-side** Vercel Production environment variables:
   - `FACEBOOK_APP_ID`: the application ID.
   - `FACEBOOK_APP_SECRET`: the secret; never expose in chat, Flutter defines,
     screenshots, source control, or browser JavaScript.
   - `FACEBOOK_GRAPH_VERSION`: a supported version selected in Meta, in the
     form `vNN.N`; do not use the test fixture version.
5. Redeploy. `/api/auth/facebook-config` should return `enabled: true` and only
   public ID/version. Test on desktop and the installed iPhone PWA with an
   authorized test account before enabling public access.

The backend validates the token's application, user, type and expiry before
issuing a HanziGo session. Missing email is rejected. An existing HanziGo email
is never silently linked to a Facebook identity: use its original login method.
Returning Facebook users retain their chosen HanziGo name and account ID.

Reference: https://developers.facebook.com/docs/facebook-login/web/
