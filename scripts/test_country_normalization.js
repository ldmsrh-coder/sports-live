#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');

const html = fs.readFileSync('index.html', 'utf8');
const app = fs.readFileSync('app.js', 'utf8');
function section(startMarker, endMarker) {
  const start = app.indexOf(startMarker);
  const end = app.indexOf(endMarker, start);
  assert.notEqual(start, -1, 'missing function: ' + startMarker);
  assert.notEqual(end, -1, 'missing boundary: ' + endMarker);
  return app.slice(start, end);
}

const labelHelpers = section('function koreanizeCommonLabel(value){', 'function formatTime(');
const labelsApi = new Function(labelHelpers + '\nreturn {koreanizeCommonLabel, ko};')();
assert.equal(labelsApi.ko('Country Confirmation Needed'), '국제/기타');
assert.equal(labelsApi.ko('Country_Check_Required'), '국제/기타');
assert.equal(labelsApi.ko('CountryConfirmationNeeded'), '국제/기타');
assert.equal(labelsApi.ko('국가 확인 필요'), '국제/기타');
assert.equal(labelsApi.ko('국가확인필요'), '국제/기타');
assert.equal(labelsApi.ko('Manchester City'), '맨체스터 시티');

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
assert.equal(api.normalizeCountryInfo({country_name: 'Country Confirmation Needed', country_code: 'KOR'}, 'NBA').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '국가 확인 필요', code: 'UNKNOWN'}, 'K League 1').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '국가확인필요'.normalize('NFD'), code: ''}, 'K League 1').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: 'Country Confirmation Needed', code: ''}, 'UEFA Champions League').name, '유럽 대항전');
assert.equal(api.normalizeCountryInfo({name: 'country check required', code: 'UNKNOWN'}, 'UEFA Champions League').code, 'EUR');
assert.equal(api.normalizeCountryInfo({name: 'Country Verification Needed', code: ''}, 'NBA').code, 'USA');
assert.ok(html.includes('id="insightPanel"'), 'live analysis panel must be present');
assert.ok(html.includes('<script src="./app.js"></script>'), 'application JavaScript must be loaded externally');
assert.ok(!/<script>([\s\S]*?)<\/script>/i.test(html), 'application JavaScript must not be inline');
assert.ok(app.includes('function updateScoreChangeLog('), 'score change detection must be present');
assert.ok(app.includes('function renderInsightPanel('), 'transparent match analysis must be present');
assert.ok(app.includes('quality-details'), 'expandable data quality diagnostics must be present');
assert.ok(app.includes('필수 항목 완성률'), 'data completeness must be reported separately from accuracy');
assert.ok(app.includes('예정 경기인데 점수가 숫자로 표시됨'), 'scheduled-score anomaly check must be present');
assert.ok(app.includes('신뢰도 점수나 경기 예측 정확도를 임의로 만들어 표시하지 않습니다'), 'the UI must avoid fabricated confidence scores');
const cspMatch = html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/);
assert.ok(cspMatch, 'Content Security Policy must be present');
assert.ok(cspMatch[1].includes("script-src 'self'") && !cspMatch[1].includes("script-src 'self' 'unsafe-inline'"), 'CSP must block inline JavaScript');
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
console.log('Country normalization, live analysis, score-change detection and CSP tests passed.');
