// Render each slide at 1920×1080 and capture screenshots + overflow audit.
// Usage: node scripts/screenshot.mjs [file://path/to/index.html]
import { chromium } from 'playwright';
import { mkdirSync } from 'fs';
import path from 'path';

const target = process.argv[2] || 'file://' + path.resolve('index.html');
const outDir = path.resolve('preview');
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({
    // use the already-cached chromium build (revision may differ from npm package default)
    executablePath: '/home/forks/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(target, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(800);

const count = await page.evaluate(() => document.querySelectorAll('.slide').length);
console.log(`slides: ${count}`);

for (let i = 0; i < count; i++) {
    await page.evaluate((idx) => {
        const slides = document.querySelectorAll('.slide');
        slides.forEach((s, j) => {
            s.classList.toggle('active', j === idx);
            s.classList.toggle('visible', j === idx);
        });
    }, i);
    await page.waitForTimeout(1300); // reveal animations settle

    // overflow audit: any descendant box beyond stage bounds (2px tolerance)
    const issues = await page.evaluate(() => {
        const bad = [];
        const slide = document.querySelector('.slide.active');
        if (!slide) return bad;
        const walk = (el) => {
            for (const child of el.children) {
                const r = child.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {
                    if (r.right > 1922 || r.bottom > 1082 || r.left < -2 || r.top < -2) {
                        bad.push({
                            tag: child.tagName.toLowerCase(),
                            cls: (child.className || '').toString().slice(0, 60),
                            rect: `L${Math.round(r.left)} T${Math.round(r.top)} R${Math.round(r.right)} B${Math.round(r.bottom)}`,
                            text: (child.textContent || '').trim().slice(0, 40),
                        });
                    }
                }
                walk(child);
            }
        };
        walk(slide);
        return bad;
    });

    const num = String(i + 1).padStart(2, '0');
    await page.screenshot({ path: path.join(outDir, `slide-${num}.png`) });
    if (issues.length) {
        console.log(`slide ${num}: OVERFLOW x${issues.length}`);
        issues.slice(0, 6).forEach(x => console.log(`   - <${x.tag} class="${x.cls}"> ${x.rect} "${x.text}"`));
    } else {
        console.log(`slide ${num}: ok`);
    }
}

await browser.close();
