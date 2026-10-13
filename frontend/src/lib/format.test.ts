import { describe, it, expect } from 'vitest';
import { inr, lakh, humanize, categoryColor, CATEGORY_COLOR } from './format';

describe('format utilities', () => {
  describe('inr', () => {
    it('formats positive numbers correctly', () => {
      expect(inr(2570000)).toBe('₹25,70,000');
      expect(inr(100)).toBe('₹100');
    });

    it('formats negative numbers correctly', () => {
      expect(inr(-2570000)).toBe('−₹25,70,000');
      expect(inr(-100)).toBe('−₹100');
    });

    it('formats zero correctly', () => {
      expect(inr(0)).toBe('₹0');
      expect(inr(-0)).toBe('₹0');
    });

    it('returns fallback for null, undefined, and NaN', () => {
      expect(inr(null)).toBe('—');
      expect(inr(undefined)).toBe('—');
      expect(inr(NaN)).toBe('—');
    });

    it('returns custom fallback when provided', () => {
      expect(inr(null, 'N/A')).toBe('N/A');
    });
  });

  describe('lakh', () => {
    it('formats crores correctly (>= 1_00_00_000)', () => {
      expect(lakh(1_00_00_000)).toBe('₹1.00 Cr');
      expect(lakh(1_50_00_000)).toBe('₹1.50 Cr');
      expect(lakh(12_34_56_789)).toBe('₹12.35 Cr');
    });

    it('formats lakhs correctly (>= 1_00_000)', () => {
      expect(lakh(1_00_000)).toBe('₹1.00 L');
      expect(lakh(2_20_000)).toBe('₹2.20 L');
      expect(lakh(99_99_999)).toBe('₹100.00 L');
    });

    it('formats thousands correctly (>= 1_000)', () => {
      expect(lakh(1_000)).toBe('₹1.0 K');
      expect(lakh(1_500)).toBe('₹1.5 K');
      expect(lakh(99_999)).toBe('₹100.0 K');
    });

    it('formats smaller numbers correctly', () => {
      expect(lakh(0)).toBe('₹0');
      expect(lakh(999)).toBe('₹999');
    });

    it('formats negative numbers correctly', () => {
      expect(lakh(-1_50_00_000)).toBe('−₹1.50 Cr');
      expect(lakh(-2_20_000)).toBe('−₹2.20 L');
      expect(lakh(-1_500)).toBe('−₹1.5 K');
      expect(lakh(-999)).toBe('−₹999');
    });

    it('returns fallback for null, undefined, and NaN', () => {
      expect(lakh(null)).toBe('—');
      expect(lakh(undefined)).toBe('—');
      expect(lakh(NaN)).toBe('—');
    });

    it('returns custom fallback when provided', () => {
      expect(lakh(null, 'N/A')).toBe('N/A');
    });
  });

  describe('humanize', () => {
    it('replaces underscores with spaces', () => {
      expect(humanize('hello_world')).toBe('hello world');
      expect(humanize('sanction_letter')).toBe('sanction letter');
      expect(humanize('no_underscores')).toBe('no underscores');
    });

    it('returns original string if no underscore is provided', () => {
      expect(humanize('hello')).toBe('hello');
    });
  });

  describe('categoryColor', () => {
    it('returns correct color for known categories', () => {
      expect(categoryColor('sanction_letter')).toBe(CATEGORY_COLOR.sanction_letter);
      expect(categoryColor('stock_statement')).toBe(CATEGORY_COLOR.stock_statement);
      expect(categoryColor('debtor_ledger')).toBe(CATEGORY_COLOR.debtor_ledger);
      expect(categoryColor('creditor_ledger')).toBe(CATEGORY_COLOR.creditor_ledger);
      expect(categoryColor('bank_statement')).toBe(CATEGORY_COLOR.bank_statement);
      expect(categoryColor('other')).toBe(CATEGORY_COLOR.other);
    });

    it('returns "other" color for unknown categories', () => {
      expect(categoryColor('unknown_category')).toBe(CATEGORY_COLOR.other);
      expect(categoryColor('')).toBe(CATEGORY_COLOR.other);
    });
  });
});
