/**
 * swipe.js — Modulo de JavaScript para simular el "swiping" de Tinder (generado con Claude)
 */

'use strict';

const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content ?? '';
const SWIPE_THRESHOLD = 80; // px to trigger a swipe

class SwipeDeck {
    constructor(candidates) {
        this.candidates = candidates;
        this.currentIndex = 0;
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;

        this.cardEl      = document.getElementById('swipe-card');
        this.nextCardEl  = document.getElementById('swipe-card-next');
        this.likeOverlay = document.getElementById('overlay-like');
        this.nopeOverlay = document.getElementById('overlay-nope');
        this.deckWrapper = document.getElementById('deck-wrapper');
        this.emptyState  = document.getElementById('empty-state');

        if (!this.cardEl) return;
        this.renderCurrent();
        this.bindEvents();
    }

    getCurrent() { return this.candidates[this.currentIndex];     }
    getNext()    { return this.candidates[this.currentIndex + 1]; }

    // ── Rendering ────────────────────────────────────────────────────────────

    renderCurrent() {
        const c = this.getCurrent();
        if (!c) { this.showEmpty(); return; }

        this.cardEl.style.transition = 'none';
        this.cardEl.style.transform  = '';
        this.cardEl.style.opacity    = '1';
        this.likeOverlay.style.opacity = '0';
        this.nopeOverlay.style.opacity = '0';

        this._fillCard(this.cardEl, c, true);
        this.renderNextPeek();
    }

    renderNextPeek() {
        if (!this.nextCardEl) return;
        const n = this.getNext();
        if (n) {
            this._fillCard(this.nextCardEl, n, false);
            this.nextCardEl.style.display = '';
        } else {
            this.nextCardEl.style.display = 'none';
        }
    }

    _fillCard(el, c, isMain) {
        const foto = el.querySelector('[data-field="foto"]');
        if (foto) foto.src = c.foto_url || '/static/default_avatar.svg';

        const nombre = el.querySelector('[data-field="nombre"]');
        if (nombre) nombre.textContent = c.nombre;

        const edad = el.querySelector('[data-field="edad"]');
        if (edad) edad.textContent = c.edad ? `${c.edad} años` : '';

        const personas = el.querySelector('[data-field="personas"]');
        if (personas) personas.textContent = c.personas_comunes > 0
            ? `${c.personas_comunes} persona${c.personas_comunes > 1 ? 's' : ''} en común`
            : '';
    }

    showEmpty() {
        if (this.deckWrapper) this.deckWrapper.style.display = 'none';
        if (this.emptyState)  this.emptyState.style.display  = 'block';
    }

    // ── Events ───────────────────────────────────────────────────────────────

    bindEvents() {
        // Mouse
        this.cardEl.addEventListener('mousedown',  e => this.onDragStart(e));
        document.addEventListener('mousemove',     e => this.onDrag(e));
        document.addEventListener('mouseup',       e => this.onDragEnd(e));

        // Touch
        this.cardEl.addEventListener('touchstart', e => this.onDragStart(e), { passive: true });
        document.addEventListener('touchmove',     e => { if (this.isDragging) e.preventDefault(); this.onDrag(e); }, { passive: false });
        document.addEventListener('touchend',      e => this.onDragEnd(e));

        // Buttons
        document.getElementById('btn-like')?.addEventListener('click', () => this.swipe('right'));
        document.getElementById('btn-nope')?.addEventListener('click', () => this.swipe('left'));

        // Keyboard
        document.addEventListener('keydown', e => {
            if (document.activeElement.tagName === 'INPUT' ||
                document.activeElement.tagName === 'TEXTAREA') return;
            if (e.key === 'ArrowRight') this.swipe('right');
            if (e.key === 'ArrowLeft')  this.swipe('left');
        });
    }

    onDragStart(e) {
        if (!this.getCurrent()) return;
        this.isDragging = true;
        const p = e.touches ? e.touches[0] : e;
        this.startX = p.clientX;
        this.startY = p.clientY;
        this.cardEl.style.transition = 'none';
        this.cardEl.style.cursor = 'grabbing';
    }

    onDrag(e) {
        if (!this.isDragging) return;
        const p = e.touches ? e.touches[0] : e;
        const dx = p.clientX - this.startX;
        const dy = p.clientY - this.startY;
        const rot = dx * 0.07;

        this.cardEl.style.transform = `translate(${dx}px, ${dy * 0.35}px) rotate(${rot}deg)`;

        const ratio = Math.min(Math.abs(dx) / SWIPE_THRESHOLD, 1);
        if (dx > 0) {
            this.likeOverlay.style.opacity = ratio;
            this.nopeOverlay.style.opacity = 0;
        } else {
            this.nopeOverlay.style.opacity = ratio;
            this.likeOverlay.style.opacity = 0;
        }
    }

    onDragEnd(e) {
        if (!this.isDragging) return;
        this.isDragging = false;
        this.cardEl.style.cursor = 'grab';
        const p = e.changedTouches ? e.changedTouches[0] : e;
        const dx = p.clientX - this.startX;

        this.cardEl.style.transition = 'transform 0.3s ease, opacity 0.3s ease';

        if (dx > SWIPE_THRESHOLD)       this.swipe('right');
        else if (dx < -SWIPE_THRESHOLD) this.swipe('left');
        else {
            this.cardEl.style.transform = '';
            this.likeOverlay.style.opacity = '0';
            this.nopeOverlay.style.opacity = '0';
        }
    }

    // ── Swipe logic ──────────────────────────────────────────────────────────

    swipe(direction) {
        const c = this.getCurrent();
        if (!c || this._swiping) return;
        this._swiping = true;

        const isRight = direction === 'right';
        this.cardEl.style.transition = 'transform 0.45s ease, opacity 0.45s ease';
        this.cardEl.style.transform  = `translate(${isRight ? '160%' : '-160%'}, -10px) rotate(${isRight ? '25deg' : '-25deg'})`;
        this.cardEl.style.opacity    = '0';
        if (isRight) this.likeOverlay.style.opacity = '1';
        else         this.nopeOverlay.style.opacity = '1';

        // Advance deck in JS, then notify the server (204 keeps us on this page)
        setTimeout(() => {
            this.currentIndex++;
            this._swiping = false;
            this.renderCurrent();

            const url = isRight ? `/aceptar/${c.id}` : `/rechazar/${c.id}`;
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = url;
            const csrf = document.createElement('input');
            csrf.type  = 'hidden';
            csrf.name  = 'csrf_token';
            csrf.value = CSRF_TOKEN;
            form.appendChild(csrf);
            document.body.appendChild(form);
            form.submit();
        }, 460);
    }
}
