import { describe, expect, it } from 'vitest';
import { registerNavConfig } from './nav-config.js';

describe('nav config', () => {
    it('registers is-active as a current link class', () => {
        const up = {
            feedback: {
                config: {
                    currentClasses: ['up-current'],
                },
            },
        };

        registerNavConfig(up);

        expect(up.feedback.config.currentClasses).toEqual(['up-current', 'is-active']);
    });

    it('does not register is-active twice', () => {
        const up = {
            feedback: {
                config: {
                    currentClasses: ['up-current', 'is-active'],
                },
            },
        };

        registerNavConfig(up);

        expect(up.feedback.config.currentClasses).toEqual(['up-current', 'is-active']);
    });
});