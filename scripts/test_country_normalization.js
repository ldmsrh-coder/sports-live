#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');

const html = fs.readFileSync('index.html', 'utf8');
const app = fs.readFileSync('app.js', 'utf8');
const workflow = fs.readFileSync('.github/workflows/update-korean-sports.yml', 'utf8');
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

const sourceHelper = section('function sourceUrl(source){', '/* Small, accessible private notes attached to a specific match. */');
const sourceApi = new Function(sourceHelper + '\nreturn {sourceUrl};')();
assert.equal(sourceApi.sourceUrl('KBO 공식 일정'), 'https://www.koreabaseball.com/Schedule/Schedule.aspx');
assert.equal(sourceApi.sourceUrl('KBO 공개 일정 데이터'), 'https://github.com/dentearl/kbo-data');
assert.equal(sourceApi.sourceUrl('SportScore 국내 농구'), 'https://sportscore.com/');
assert.equal(sourceApi.sourceUrl('알 수 없는 출처'), '');
assert.ok(app.includes('target="_blank" rel="noopener noreferrer"'), 'source links must use safe new-window attributes');

const countryFromName = section('function countryFromName(value){', 'function normalizeCountryInfo(');
const normalizer = section('function normalizeCountryInfo(', 'function countryForLeague(');
const countryForLeague = section('function countryForLeague(', 'function flagHtml(');
const api = new Function(countryFromName + '\n' + countryForLeague + '\n' + normalizer + '\nreturn {countryFromName, normalizeCountryInfo};')();

assert.equal(api.countryFromName('Country Confirmation Needed').name, '국제/기타');
assert.equal(api.countryFromName('  COUNTRY   CONFIRMATION NEEDED — upstream feed ').name, '국제/기타');
assert.equal(api.countryFromName('country-check-required: provider label').name, '국제/기타');
assert.equal(api.countryFromName('CountryIdentificationNeeded').name, '국제/기타');
assert.equal(api.countryFromName('국가 확인 필요\u200B — 제공처').name, '국제/기타');
assert.equal(api.countryFromName('Country_Check_Required').name, '국제/기타');
assert.equal(api.countryFromName('국가 확인 필요').name, '국제/기타');
assert.equal(api.countryFromName('국가확인필요').name, '국제/기타');
assert.equal(api.countryFromName('국가 확인 필요 - upstream feed').name, '국제/기타');
assert.equal(api.countryFromName('Country confirmation needed: provider label').name, '국제/기타');
assert.equal(api.countryFromName('국가 확인 필요 - upstream feed').name, '국제/기타');
assert.equal(api.countryFromName('Country confirmation needed: provider label').name, '국제/기타');
assert.equal(api.normalizeCountryInfo({name: 'Country Confirmation Needed', code: 'USA'}, 'NBA').code, 'USA');
assert.equal(api.normalizeCountryInfo({name: '국가확인필요', code: 'KOR'}, 'K리그').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: 'Japan', code: 'JPN'}, 'International Friendly').code, 'JPN');
assert.equal(api.normalizeCountryInfo({name: 'Unknown Country', code: ''}, 'UEFA Champions League').code, 'EUR');
assert.equal(api.normalizeCountryInfo(null, 'K League 1').code, 'KOR');
assert.equal(api.normalizeCountryInfo({country_name: 'Country Confirmation Needed', country_code: 'KOR'}, 'NBA').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '국가 확인 필요', code: 'UNKNOWN'}, 'K League 1').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '국가확인필요'.normalize('NFD'), code: ''}, 'K League 1').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: 'Country Confirmation Needed', code: ''}, 'UEFA Champions League').name, '유럽 대항전');
assert.equal(api.normalizeCountryInfo({name: 'Country confirmation needed: provider label', code: 'REQ'}, 'K League 1').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '국가 확인 필요 - upstream feed', code: 'REQ'}, 'NBA').code, 'USA');
assert.equal(api.normalizeCountryInfo({name: 'Country_Check_Required', code: 'REQ'}, 'UEFA Champions League').code, 'EUR');
assert.equal(api.normalizeCountryInfo({name: 'country check required', code: 'UNKNOWN'}, 'UEFA Champions League').code, 'EUR');
assert.equal(api.normalizeCountryInfo({name: 'Country Verification Needed', code: ''}, 'NBA').code, 'USA');
assert.equal(api.normalizeCountryInfo({name: 'Country not set', code: ''}, 'K League 1').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '  COUNTRY   CONFIRMATION NEEDED — upstream feed ', code: ''}, 'Unknown League').name, '국제/기타');
assert.equal(api.normalizeCountryInfo({country: {name: 'Country Check Required', code: 'KOR'}}, 'Unknown League').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '국가   확인 필요 — 제공처', code: ''}, 'Unknown League').name, '국제/기타');
assert.equal(api.normalizeCountryInfo({name: '  Unknown Country  ', code: 'USA'}, 'NBA').code, 'USA');
assert.equal(api.normalizeCountryInfo({name: '국가 확인', code: ''}, 'K League 1').code, 'KOR');
assert.ok(html.includes('id="connectionBadge"'), 'live connection status badge must be present');
assert.ok(app.includes('데이터 확인 완료 · 90초 자동 확인'), 'successful data refresh should be visible');
assert.ok(app.includes("refreshInterval=selectedSport!=='all'&&hasLiveMatch?30000:90000"), 'specific-sport live matches should refresh more frequently without increasing all-sports provider load');
assert.ok(html.includes('id="scoreAlerts"'), 'score alert opt-in control must be present');
assert.ok(app.includes('function toggleScoreAlerts(') && app.includes('function notifyScoreChanges('), 'score notifications must be opt-in and driven by observed score changes');
assert.ok(app.includes('/저장된 일정|캐시|cache/i.test(String(source||\'\'))'), 'stale cached schedules must not trigger score notifications');
assert.ok(app.includes("localStorage.setItem(SCORE_ALERT_PREF,'1')"), 'score alert preference must be saved locally');
assert.ok(html.includes('id="insightPanel"'), 'live analysis panel must be present');
assert.ok(/<script src="\.\/app\.js(?:\?[^\"]*)?"><\/script>/.test(html), 'application JavaScript must be loaded externally and may use cache busting');
assert.ok(!/<script>([\s\S]*?)<\/script>/i.test(html), 'application JavaScript must not be inline');
assert.ok(app.includes('function updateScoreChangeLog('), 'score change detection must be present');
assert.ok(app.includes('function renderInsightPanel('), 'transparent match analysis must be present');
assert.ok(app.includes("games.forEach(g=>{g.country=normalizeCountryInfo(g.country,g.league,g.home,g.away);"), 'country placeholders must be normalized again immediately before rendering');
assert.ok(app.includes('function sourceUrl(source)'), 'per-match source links must be available');
const csvHelper = section('function csvCell(value){', 'function exportVisibleCsv(){');
const csvApi = new Function(csvHelper + '\nreturn {csvCell};')();
assert.equal(csvApi.csvCell('=1+1'), '"\'=1+1"');
assert.equal(csvApi.csvCell('+SUM(A1:A2)'), '"\'+SUM(A1:A2)"');
assert.equal(csvApi.csvCell('-'), '"-"');
assert.equal(csvApi.csvCell('12'), '"12"');

assert.ok(app.includes('sourceUrl(g.source)'), 'match cards must link to their data source');
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

const probabilityHelpers = section('function canShowProbability(g){', 'function probabilityDetails(g){');
const probabilityApi = new Function(probabilityHelpers + '\nreturn {canShowProbability};')();
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: false}), true);
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: true, probabilityConfidence: 'low', modelDetails: {historyGames: 6, homeStats: {played: 2}, awayStats: {played: 4}}}), false);
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: true, probabilityConfidence: 'low', modelDetails: {historyGames: 5, homeStats: {played: 2}, awayStats: {played: 3}}}), false);
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: true, probabilityConfidence: 'very-low', modelDetails: {historyGames: 20, homeStats: {played: 10}, awayStats: {played: 10}}}), false);
assert.ok(app.includes('function localPredictionBacktest('), 'local historical prediction validation must be present');
assert.ok(app.includes('return h>=3&&a>=3&&n>=12'), 'low-sample estimates must be withheld until both teams have enough history');
assert.ok(app.includes('scoredAverage'), 'team scoring averages should be available to explain estimates');
assert.ok(app.includes('venueDiff'), 'home/away performance should contribute to estimates');
assert.ok(app.includes('restDiff'), 'rest-day difference should contribute to estimates');
assert.ok(app.includes('function localPredictionBacktest('), 'historical predictions should be evaluated against final results');

assert.ok(workflow.includes('for attempt in 1 2 3; do') && workflow.includes('git rebase origin/main') && workflow.includes('git push origin HEAD:main'), 'snapshot publish retries concurrent updates');
assert.ok(html.includes('id="requestAudit"'), 'visible live request audit panel must be present');
assert.ok(app.includes('Transparent request audit:'), 'real fetch requests must be instrumented');
const privateNotes = section('/* Private per-browser match notes:', 'function esc(v){');
assert.ok(privateNotes.includes("localStorage.setItem(MATCH_NOTES_KEY"), 'match notes must be stored locally');
assert.ok(privateNotes.includes("slice(0,1000)"), 'match notes must be length-limited');
assert.ok(privateNotes.includes("Object.entries(raw).slice(-500)"), 'loaded notes must be capped');
assert.ok(privateNotes.includes("replace(/[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]/g,'')") || privateNotes.includes("replace(/[\\u0000-\\u0008\\u000B\\u000C\\u000E-\\u001F]/g,'')"), 'control characters must be removed from notes');
assert.ok(!/\bfetch\s*\(/i.test(privateNotes) && !/XMLHttpRequest/i.test(privateNotes), 'private notes must not be sent to a server');

assert.ok(app.includes("'HTTP '+response.status"), 'HTTP response status should be visible in the live request monitor');
assert.ok(app.includes('requestAuditLog.failed++'), 'failed requests must be counted instead of hiding errors');
assert.ok(app.includes("Date.now()-entry.startedAt") && app.includes('최근 요청 실패'), 'request monitor should show latency and the latest request failure');
assert.ok(app.includes('pending:0') && app.includes('requestAuditLog.pending=Math.max(0,requestAuditLog.pending-1)'), 'pending requests are counted independently of the shortened visible log');
assert.ok(app.includes("['sport','date','dates','competition','league','limit','q']"), 'request monitor should only show an allowlist of harmless query fields');
assert.ok(html.includes('HTTP 성공은 데이터의 정확성'), 'request monitor must not imply HTTP success guarantees data accuracy');

console.log('Country normalization, live analysis, request audit, score-change detection and CSP tests passed.');
