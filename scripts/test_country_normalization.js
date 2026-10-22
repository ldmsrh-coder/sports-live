#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');

const html = fs.readFileSync('index.html', 'utf8');
const app = fs.readFileSync('app.js', 'utf8');
const workflow = fs.readFileSync('.github/workflows/update-korean-sports.yml', 'utf8');
const serviceWorker = fs.readFileSync('sw.js', 'utf8');
const manifest = JSON.parse(fs.readFileSync('manifest.webmanifest', 'utf8'));
function section(startMarker, endMarker) {
  const start = app.indexOf(startMarker);
  const end = app.indexOf(endMarker, start);
  assert.notEqual(start, -1, 'missing function: ' + startMarker);
  assert.notEqual(end, -1, 'missing boundary: ' + endMarker);
  return app.slice(start, end);
}

const labelHelpers = section('function koreanizeCommonLabel(value){', 'function formatTime(');
const labelsApi = new Function(labelHelpers + '\nreturn {koreanizeCommonLabel, ko};')();
assert.equal(labelsApi.ko('Country Confirmation Needed'), '국가 미확인');
assert.equal(labelsApi.koreanizeCommonLabel('Country Confirmation Needed'), '국가 미확인');
assert.equal(labelsApi.ko('Country_Check_Required'), '국가 미확인');
assert.equal(labelsApi.ko('CountryConfirmationNeeded'), '국가 미확인');
assert.equal(labelsApi.ko('국가 확인 필요'), '국가 미확인');
assert.equal(labelsApi.ko('국가확인필요'), '국가 미확인');
assert.equal(labelsApi.ko('Manchester City'), '맨체스터 시티');

const sourceHelper = section('function sourceUrl(source){', '/* Small, accessible private notes attached to a specific match. */');
const sourceApi = new Function(sourceHelper + '\nreturn {sourceUrl};')();
assert.equal(sourceApi.sourceUrl('KBO 공식 일정'), 'https://www.koreabaseball.com/Schedule/Schedule.aspx');
assert.equal(sourceApi.sourceUrl('KBO 공개 일정 데이터'), 'https://github.com/dentearl/kbo-data');
assert.equal(sourceApi.sourceUrl('SportScore 국내 농구'), 'https://sportscore.com/');
assert.equal(sourceApi.sourceUrl('알 수 없는 출처'), '');
assert.ok(app.includes('target="_blank" rel="noopener noreferrer"'), 'source links must use safe new-window attributes');

const countryFromName = section('function countryFromName(value){', 'function normalizeCountryInfo(');
const normalizer = section('function normalizeCountryInfo(', 'function isCountryUnresolved(');
const countryForLeague = section('function countryForLeague(', 'function flagHtml(');
const unresolvedHelper = section('function isCountryUnresolved(', 'function countryForLeague(');
const api = new Function(countryFromName + '\n' + countryForLeague + '\n' + normalizer + '\n' + unresolvedHelper + '\nreturn {countryFromName, normalizeCountryInfo, countryForLeague, isCountryUnresolved};')();

assert.equal(api.countryFromName('Country Confirmation Needed').name, '국가 미확인');
assert.equal(api.countryFromName('CountryConfirmationNeeded').name, '국가 미확인');
assert.equal(api.countryFromName('CountryIdentificationNeeded').name, '국가 미확인');
assert.equal(api.countryFromName('CountryCheckRequired').name, '국가 미확인');
assert.equal(api.normalizeCountryInfo({name: 'CountryConfirmationNeeded', code: ''}, 'Unknown League').name, '국가 미확인');
assert.equal(api.countryFromName('  COUNTRY   CONFIRMATION NEEDED — upstream feed ').name, '국가 미확인');
assert.equal(api.countryFromName('country-check-required: provider label').name, '국가 미확인');
assert.equal(api.countryFromName('CountryIdentificationNeeded').name, '국가 미확인');
assert.equal(api.countryFromName('국가 확인 필요\u200B — 제공처').name, '국가 미확인');
assert.equal(api.countryFromName('Country_Check_Required').name, '국가 미확인');
assert.equal(api.countryFromName('Country not found').code, 'UNK');
assert.equal(api.countryFromName('Country unavailable').code, 'UNK');
assert.equal(api.countryFromName('Needs country verification').code, 'UNK');
assert.equal(api.normalizeCountryInfo({name:'Country check required — provider label', code:''}, 'Mystery Tournament').name, '국가 미확인');
assert.ok(html.includes('app.js?v=20261022-stability-19'), 'updated app must invalidate cached application JavaScript');
assert.equal(api.countryFromName('국가 확인 필요').name, '국가 미확인');
assert.equal(api.countryFromName('국가확인필요').name, '국가 미확인');
assert.equal(api.isCountryUnresolved({name:'국가확인필요', code:'UNK'}), true);
assert.equal(api.isCountryUnresolved({name:'대한민국', code:'KOR'}), false);
assert.equal(api.countryForLeague('Romania Liga I').code, 'ROU');
assert.equal(api.countryForLeague('AS Roma').code, 'ITA');
assert.equal(api.countryForLeague('United Arab Emirates Pro League').code, 'UAE');
assert.equal(api.countryForLeague('Finland Veikkausliiga').code, 'FIN');
assert.equal(api.countryForLeague('Serie A AS Roma').code, 'ITA');
assert.equal(api.countryForLeague('Mystery Tournament').code, 'UNK');
assert.equal(api.countryFromName('Bulgaria').code, 'BUL');
assert.equal(api.countryFromName('COD').name, '콩고민주공화국');
assert.equal(api.countryForLeague('Bosnia Premier League').code, 'BIH');
assert.equal(api.countryForLeague('Singapore Premier League').code, 'SIN');
assert.equal(api.countryForLeague('Oman Professional League').code, 'OMA');
assert.equal(api.countryForLeague('Romania Liga I').code, 'ROU');
assert.equal(api.countryForLeague('International Friendly').code, 'INT');


assert.equal(api.countryFromName('United Arab Emirates').code, 'UAE');
assert.equal(api.countryFromName('ROU').name, '루마니아');
assert.equal(api.countryFromName('Finland').code, 'FIN');
assert.equal(api.countryFromName('Taiwan').code, 'TPE');
assert.equal(api.countryFromName('홍콩').code, 'HKG');
const historyHelpers = section('function historicalSportKey(g){', 'async function applyCachedHistoryModel(');
const historyApi = new Function(historyHelpers + '\nreturn {historicalSportKey,historicalMatchKey,historicalDuplicateIndex};')();
assert.equal(historyApi.historicalSportKey({sport:'soccer'}), 'football');
assert.equal(historyApi.historicalSportKey({sport:'americanfootball'}), 'americanfootball');
assert.equal(historyApi.historicalSportKey({sportCategory:'football',leagueKey:'nfl.1'}), 'americanfootball');
assert.equal(historyApi.historicalSportKey({sport:'tabletennis'}), 'table-tennis');
assert.equal(historyApi.historicalDuplicateIndex([{time:''}], '19:00'), 0, 'missing kickoff time should merge with a known kickoff');
assert.equal(historyApi.historicalDuplicateIndex([{time:'19:00'}], ''), 0, 'a missing kickoff should not duplicate a known event');
assert.equal(historyApi.historicalDuplicateIndex([{time:'19:00'}], '19:00'), 0, 'identical kickoff should deduplicate');
assert.equal(historyApi.historicalDuplicateIndex([{time:'19:00'}], '20:00'), -1, 'distinct kickoff times preserve doubleheaders');
const normHistory = value => String(value||'').toLowerCase().replace(/[^a-z0-9]/g,'');
assert.equal(historyApi.historicalMatchKey({time:'19:00'},'football','2026-10-01','Home Team','Away Team',2,1,normHistory),historyApi.historicalMatchKey({time:'오후 19:00'},'football','2026-10-01','Home-Team','Away Team',2,1,normHistory),'duplicate cache copies of the same completed match should share a key');
assert.notEqual(historyApi.historicalMatchKey({time:'19:00'},'football','2026-10-01','Home Team','Away Team',2,1,normHistory),historyApi.historicalMatchKey({time:'19:00'},'americanfootball','2026-10-01','Home Team','Away Team',2,1,normHistory),'soccer and American football histories must never be mixed');
const sanitizerHelper = section('function containsCountryPlaceholder(value){', 'function normalize(raw){');
const sanitizerApi = new Function('ko','normalizeCountryInfo',sanitizerHelper+'\nreturn {containsCountryPlaceholder,sanitizeProviderField,sanitizeGameRecord};')(labelsApi.ko,api.normalizeCountryInfo);
assert.equal(sanitizerApi.containsCountryPlaceholder('Country Confirmation Needed'), true);
assert.equal(sanitizerApi.containsCountryPlaceholder('Country_Check_Required'), true);
assert.equal(sanitizerApi.containsCountryPlaceholder('국가 확인 필요\u200B'), true);
assert.equal(sanitizerApi.containsCountryPlaceholder('국가 확인이 필요합니다'), true, 'natural Korean placeholder variants must be blocked');
assert.equal(sanitizerApi.containsCountryPlaceholder('국가 미확인'), false, 'the safe Korean fallback label must not be mistaken for a raw provider placeholder');
assert.equal(sanitizerApi.containsCountryPlaceholder('국가 미분류'), false, 'the safe Korean fallback label must remain stable');
assert.equal(sanitizerApi.containsCountryPlaceholder('국가 확인 필요 - 제공처'), true, 'provider suffixes must not leak into country labels');
assert.equal(sanitizerApi.containsCountryPlaceholder('Country status: confirmation required'), true, 'English provider placeholder variants must be blocked');
const renderStart = app.indexOf('function render(){');
assert.ok(renderStart >= 0 && app.slice(renderStart, renderStart + 900).indexOf('allGames=allGames.map') < app.slice(renderStart, renderStart + 900).indexOf('syncCountryFilterOptions()'), 'render must sanitize legacy/cached records before building country filters');
assert.equal(sanitizerApi.containsCountryPlaceholder('Premier League'), false);
assert.equal(sanitizerApi.sanitizeProviderField('Country Confirmation Needed','대회 정보 미제공'),'대회 정보 미제공');
const sanitizedGame=sanitizerApi.sanitizeGameRecord({home:'Country Confirmation Needed',away:'Unknown Opponent',league:'Country_Check_Required',country:{name:'Country Confirmation Needed',code:'UNK'},status:'예정',time:'시간 미정',source:'SportScore'});
assert.equal(sanitizedGame.home,'팀 정보 미제공');
assert.equal(sanitizedGame.league,'대회 정보 미제공');
assert.equal(sanitizedGame.country.name,'국가 미확인');
assert.equal(sanitizedGame.country.code,'UNK');
assert.ok(![sanitizedGame.home,sanitizedGame.away,sanitizedGame.league,sanitizedGame.country.name].some(sanitizerApi.containsCountryPlaceholder),'provider placeholders must never leak into visible match labels');
const flagHelper = section('function flagHtml(country){', 'function competitionLabel(');
const flagApi = new Function('esc', flagHelper + '\nreturn {flagHtml};')(value => String(value));
assert.ok(flagApi.flagHtml({code: 'ROU', flag: '🇷🇴'}).includes('flagcdn.com/24x18/ro.png'));
assert.ok(flagApi.flagHtml({code: 'UAE', flag: '🇦🇪'}).includes('flagcdn.com/24x18/ae.png'));
assert.ok(html.includes('app.js?v=20261022-pwa-countryfix-18'), 'country normalization update must bust stale browser caches');
assert.ok(html.includes('rel="manifest" href="./manifest.webmanifest"'), 'PWA manifest must be linked from the page');
assert.equal(manifest.lang, 'ko-KR');
assert.equal(manifest.start_url, './');
assert.ok(manifest.icons.some(icon => icon.src === './icons/sports-live.svg'));
assert.ok(app.includes("navigator.serviceWorker.register(new URL('./sw.js'"), 'service worker should register relative to GitHub Pages subpath');
assert.ok(serviceWorker.includes("if (url.origin !== self.location.origin) return;"), 'service worker must never cache cross-origin sports API responses');
assert.ok(serviceWorker.includes("fetch(request)"), 'service worker must try the network first to avoid stale live data');
assert.doesNotThrow(() => new Function(serviceWorker), 'service worker syntax must be valid');

assert.equal(api.countryFromName('국가 확인 필요 - upstream feed').name, '국가 미확인');
assert.equal(api.countryFromName('Country confirmation needed: provider label').name, '국가 미확인');
assert.equal(api.countryFromName('국가 확인 필요 - upstream feed').name, '국가 미확인');
assert.equal(api.countryFromName('Country confirmation needed: provider label').name, '국가 미확인');
assert.equal(api.normalizeCountryInfo({name: 'Country Confirmation Needed', code: 'USA'}, 'NBA').code, 'USA');
assert.equal(api.normalizeCountryInfo({name: '국가확인필요', code: 'KOR'}, 'K리그').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: 'Country Confirmation Needed', code: 'international'}, 'K League 1').code, 'KOR', 'known league country must override a generic international placeholder');
assert.equal(api.normalizeCountryInfo({name: 'Country Confirmation Needed', code: ''}, 'Mystery Tournament').code, 'UNK', 'unknown countries must remain unresolved instead of being guessed');
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
assert.equal(api.normalizeCountryInfo({name: '  COUNTRY   CONFIRMATION NEEDED — upstream feed ', code: ''}, 'Unknown League').name, '국가 미확인');
assert.equal(api.normalizeCountryInfo({country: {name: 'Country Check Required', code: 'KOR'}}, 'Unknown League').code, 'KOR');
assert.equal(api.normalizeCountryInfo({name: '국가   확인 필요 — 제공처', code: ''}, 'Unknown League').name, '국가 미확인');
assert.equal(api.normalizeCountryInfo({name: '  Unknown Country  ', code: 'USA'}, 'NBA').code, 'USA');
assert.equal(api.normalizeCountryInfo({name: '국가 확인', code: ''}, 'K League 1').code, 'KOR');
assert.ok(html.includes('id="connectionBadge"'), 'live connection status badge must be present');
assert.ok(app.includes('초 자동 확인') && app.includes("cb.textContent=errors.length?'일부 출처 응답 실패':'데이터 확인 완료 · '+(sport!=='all'&&games.some(isLiveGame)?'30':'90')+'초 자동 확인'"), 'successful refresh should disclose partial provider failures');
assert.ok(app.includes("refreshInterval=selectedSport!=='all'&&hasLiveMatch?30000:90000"), 'specific-sport live matches should refresh more frequently without increasing all-sports provider load');
assert.ok(html.includes('id="countryFilter"'), 'country filter control must be present');
assert.ok(app.includes('function syncCountryFilterOptions(') && app.includes("searchParams.set('country',countryFilterValue)"), 'country filtering should sync to shared links');
assert.ok(app.includes("cf=countryFilterValue||'all'") && app.includes("activeCountry==='all'"), 'country filtering must apply to screen and export data');
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

const countdownHelpers = section('function kickoffTimestamp(g){', 'function formatTime(');
const countdownApi = new Function('isLiveGame', 'isFinishedGame', countdownHelpers + '\nreturn {kickoffTimestamp, kickoffCountdownText};')(
  g => /진행|live|half/i.test(String(g.status || '')) && !/종료/.test(String(g.status || '')),
  g => /종료|finished|final/.test(String(g.status || ''))
);
const futureDay = new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10);
assert.ok(countdownApi.kickoffTimestamp({date: futureDay, time: '12:00', status: '예정'}) > Date.now(), 'near-future scheduled matches should have a countdown');
assert.equal(countdownApi.kickoffTimestamp({date: futureDay, time: '12:00', status: '취소'}), 0, 'cancelled matches must not show a kickoff countdown');
assert.equal(countdownApi.kickoffCountdownText(3600000, 0), '시작까지 1시간 0분');
assert.equal(countdownApi.kickoffCountdownText(60000, 0), '시작까지 1분');
assert.ok(app.includes('function updateKickoffCountdowns(') && app.includes('data-kickoff'), 'kickoff countdowns should update without repeated network requests');

const probabilityHelpers = section('function canShowProbability(g){', 'function probabilityDetails(g){');
const probabilityApi = new Function(probabilityHelpers + '\nreturn {canShowProbability};')();
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: false}), true);
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: true, probabilityConfidence: 'low', modelDetails: {historyGames: 6, homeStats: {played: 2}, awayStats: {played: 4}}}), false);
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: true, probabilityConfidence: 'low', modelDetails: {historyGames: 5, homeStats: {played: 2}, awayStats: {played: 3}}}), false);
assert.equal(probabilityApi.canShowProbability({homeProb: 60, awayProb: 40, probabilityIsEstimate: true, probabilityConfidence: 'very-low', modelDetails: {historyGames: 20, homeStats: {played: 10}, awayStats: {played: 10}}}), false);
assert.ok(app.includes('function localPredictionBacktest('), 'local historical prediction validation must be present');
assert.ok(app.includes("return g.probabilityConfidence==='high'||g.probabilityConfidence==='medium'"), 'low-confidence estimates must be withheld');
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

// Regression guards for visible placeholder wording, cache-bust consistency, and KST midnight rollover.
assert.ok(!app.includes("'국가 확인/검증 필요 같은 임시 문구"), 'diagnostics must not expose raw country-confirmation placeholder wording');
assert.ok(!app.includes("'화면에 노출될 경기 필드에서 국가 확인 필요류"), 'success diagnostics must use neutral country-classification wording');
const appVersion = (html.match(/<script src="\.\/app\.js\?v=([^"]+)"><\/script>/) || [])[1];
assert.ok(appVersion, 'app script must have a cache-busting version');
assert.ok(serviceWorker.includes('./app.js?v=' + appVersion), 'service worker shell must reference the exact app script version');
assert.ok(/const CACHE_VERSION\s*=\s*'20261022-19'/.test(serviceWorker), 'service worker cache version must be bumped with the app');
assert.ok(app.includes('const currentKstDate=seoulDate();if(currentKstDate!==localDate)'), 'long-open pages must roll over to the new Korea-local date');
assert.ok(app.includes('Date.now()-lastAutoRefreshAt>=15000'), 'tab visibility refresh should avoid duplicate bursts');
assert.ok(workflow.includes('cp sw.js docs/sw.js') && workflow.includes('cp manifest.webmanifest docs/manifest.webmanifest') && workflow.includes('cp icons/sports-live.svg docs/icons/sports-live.svg'), 'Pages sync must include service worker, manifest, and app icon');
