import time
from datetime import date, timedelta
from backend.app.reconciliation.schemas import Invoice, Receipt
from backend.app.reconciliation.debtor_reconciliation import _reconcile_one_debtor

def run_benchmark():
    num_invoices = 10000
    num_receipts = 10000

    invoices = []
    receipts = []
    base_date = date(2020, 1, 1)

    print("Generating data...")
    for i in range(num_invoices):
        invoices.append(Invoice(
            invoice_id=f"inv-{i}",
            debtor_name="debtor",
            date=base_date + timedelta(days=i),
            amount=10.0
        ))

    for i in range(num_receipts):
        receipts.append(Receipt(
            receipt_id=f"rec-{i}",
            debtor_name="debtor",
            date=base_date + timedelta(days=i),
            amount=10.0,
            matched_invoice_id=None
        ))

    print("Starting benchmark...")
    start = time.time()
    _reconcile_one_debtor(invoices, receipts, 30.0, base_date + timedelta(days=num_invoices))
    end = time.time()
    print(f"Time taken: {end - start:.4f} seconds")

if __name__ == "__main__":
    run_benchmark()
