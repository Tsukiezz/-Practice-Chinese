'use strict';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (event) => {
  // Let API, files, audio, uploads and third-party authentication pass through.
  if (event.request.mode !== 'navigate' || event.request.method !== 'GET'
      || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(fetch(event.request).catch(() => new Response(`<!doctype html>
<html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#153E35"><title>HanziGo · Chưa có kết nối</title>
<style>body{margin:0;background:#f5f7f4;color:#153e35;font:17px/1.6 system-ui;padding:24px}main{max-width:480px;margin:12vh auto}a{display:inline-block;background:#153e35;color:white;padding:12px 24px;border-radius:14px;text-decoration:none}</style>
<main><h1>HanziGo đang chờ kết nối</h1><p>Bật Wi-Fi hoặc dữ liệu di động để tiếp tục học. Các chức năng AI và dữ liệu tài khoản cần Internet.</p><a href="">Thử lại</a></main></html>`, {
    status: 503, headers: {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store'},
  })));
});
