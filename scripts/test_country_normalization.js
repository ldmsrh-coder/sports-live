#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');

const html = fs.readFileSync('index.html', 'utf8');
function section(startMarker, endMarker) {
  const start = html.indexOf(startMarker);
  const end = html.indexOf(endMarker, start);
  assert.notEqual(start, -1, 'missing function: ' + startMarker);
  assert.notEqual(end, -1, 'missing boundary: ' + endMarker);
  return html.slice(start, end);
}

const countryFromName = section('function countryFromName(value){', 'function normalizeCountryInfo(');
const normalizer = section('function normalizeCountryInfo(', 'function countryForLeague(');
const countryForLeague = section('function countryForLeague(', 'function flagHtml(');
const api = new Function(countryFromName + '\n' + countryForLeague + '\n' + normalizer + '\nreturn {countryFromName, normalizeCountryInfo};')();

assert.equal(api.countryFromName('Country Confirmation Needed').name, '국제/기타');
assert.equal(api.countryFromName('Country_Check_Required').name, '국제/기타');
assert.equal(api.countryFromName('국가 확인 필요').name, '국제/기타');
assert.equal(api.countryFromName('국가확인필요').name, '국제/기타');
assert.equal(api.normalizeCountryInfo({name: 'Country Confirmation Needed', code: 'USA'}, 'NBA').code, 'USA');
assert.equal(api.normalizeCountryInfo({name: '국가확인필요', code: 'KOR'}, 'K리그').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: 'Japan', code: 'JPN'}, 'International Friendly').code, 'JPN');
assert.equal(api.normalizeCountryInfo({name: 'Unknown Country', code: ''}, 'UEFA Champions League').code, 'EUR');
assert.equal(api.normalizeCountryInfo(null, 'K League 1').code, 'KOR');
const cspMatch = html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/);
assert.ok(cspMatch, 'Content Security Policy must be present');
const csp = cspMatch[1];
const connectSrc = (csp.match(/connect-src ([^;]+)/) || [])[1] || '';
for (const host of [
  'sportscore.com', 'site.api.espn.com', 'raw.githubusercontent.com',
  'user-api.kovo.co.kr', 'm.kbl.or.kr', 'www.wkbl.or.kr', 'www.kfa.or.kr',
  'www.kleague.com', 'www.koreabaseball.com', 'www.koreahandball.com'
]) {
  assert.ok(connectSrc.includes('https://' + host), 'CSP connect-src must allow ' + host);
}
assert.ok(!/connect-src https:(;|$)/.test(csp), 'CSP connect-src must not allow every HTTPS host');
assert.ok(csp.includes("img-src 'self' data: https://flagcdn.com"), 'CSP should restrict flag images to the flag provider');
console.log('Country normalization and CSP tests passed (9 country cases + policy checks).');
