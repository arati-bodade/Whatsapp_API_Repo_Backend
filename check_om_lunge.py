import sys
sys.path.append('.')
from db.session import SessionLocal
from models.credit_distribution import CreditDistribution
from models.reseller import Reseller

db = SessionLocal()

print('=== Checking Reseller Credit Distributions ===')

# Check all credit distributions from this reseller
reseller_id = '62a65ac1-5864-469c-bf4e-fb92d5c3b8e4'
distributions = db.query(CreditDistribution).filter(
    CreditDistribution.from_reseller_id == reseller_id
).all()

print(f'Total distributions from reseller {reseller_id}: {len(distributions)}')

for i, dist in enumerate(distributions):
    print(f'  {i+1}. {dist.credits_shared} credits to {dist.to_business_user_id} on {dist.shared_at}')

# Check if there's a distribution to Om Lunge that wasn't applied
om_lunge_id = 'c83ca739-3e10-42ea-aaa0-be59640ce872'
om_lunge_dist = db.query(CreditDistribution).filter(
    CreditDistribution.from_reseller_id == reseller_id,
    CreditDistribution.to_business_user_id == om_lunge_id
).first()

if om_lunge_dist:
    print(f'\n✅ Found distribution to Om Lunge:')
    print(f'  Credits: {om_lunge_dist.credits_shared}')
    print(f'  Date: {om_lunge_dist.shared_at}')
else:
    print(f'\n❌ No credit distribution found for Om Lunge')

# Check reseller's available credits
reseller = db.query(Reseller).filter(Reseller.reseller_id == reseller_id).first()
if reseller:
    print(f'\nReseller Status:')
    print(f'  Available Credits: {reseller.available_credits}')
    print(f'  Total Credits: {reseller.total_credits}')

db.close()
