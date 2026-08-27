// Export the deck to a 14-page 1920×1080 PDF via Chromium print pipeline.
// Usage: node scripts/export-pdf.mjs
import { chromium } from 'playwright';
import path from 'path';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto('file://' + path.resolve('index.html'), { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(1200);

await page.pdf({
    path: path.resolve('slides.pdf'),
    width: '1920px',
    height: '1080px',
    printBackground: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
    pageRanges: '',
});

await browser.close();
console.log('slides.pdf written');
