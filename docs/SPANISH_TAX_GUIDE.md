# Spanish Tax Compliance Guide

## Overview

This guide explains how Crypto DB handles Spanish tax compliance for cryptocurrency transactions.

## Tax Regulations in Spain

### Capital Gains Tax

Cryptocurrency sales in Spain are subject to capital gains tax with the following brackets:

| Income Range | Tax Rate |
|--------------|----------|
| Up to €6,000 | 19% |
| €6,000 - €50,000 | 21% |
| €50,000 - €200,000 | 23% |
| Over €200,000 | 26% |

### Cost Basis Calculation

Spain uses the **FIFO (First In, First Out)** method for calculating the cost basis of cryptocurrency sales. This means:

1. The first units purchased are considered the first units sold
2. The acquisition cost of the oldest units determines your cost basis
3. Any gain or loss is calculated based on this cost basis

## Required Tax Forms

### Modelo 100 (IRPF)

Annual income tax return that includes capital gains from cryptocurrency transactions.

**Required Information:**
- Total capital gains
- Total capital losses
- Net result (gains - losses)
- Detailed transaction history

### Modelo 720

Declaration of assets abroad required if:
- Total cryptocurrency holdings exceed €50,000
- Holdings are in foreign platforms/exchanges

## Using Crypto DB for Tax Compliance

### Generate Annual Tax Report

```bash
python -m crypto_db.cli tax report --year 2024
```

This command generates a comprehensive tax report including:
- Total capital gains and losses
- Net taxable amount
- Estimated tax liability
- FIFO-based transaction breakdown

### Calculate Capital Gains

```bash
python -m crypto_db.cli tax gains --year 2024
```

This shows detailed capital gains calculations with:
- Individual transaction gains/losses
- Cost basis for each sale
- Remaining holdings after sales

## Example Scenario

### Transactions

1. **January 15, 2024**: Buy 1 BTC at €40,000
2. **March 20, 2024**: Buy 1 BTC at €45,000
3. **June 10, 2024**: Sell 1.5 BTC at €50,000

### FIFO Calculation

**Sale proceeds**: 1.5 BTC × €50,000 = €75,000

**Cost basis (FIFO)**:
- 1.0 BTC @ €40,000 = €40,000 (from first purchase)
- 0.5 BTC @ €45,000 = €22,500 (from second purchase)
- Total cost basis = €62,500

**Capital gain**: €75,000 - €62,500 = €12,500

**Tax calculation**:
- First €6,000 @ 19% = €1,140
- Remaining €6,500 @ 21% = €1,365
- **Total tax**: €2,505

**Remaining holdings**: 0.5 BTC @ €45,000 cost basis

## Best Practices

### Record Keeping

1. **Keep all transaction records**: Platform statements, transfer confirmations
2. **Document acquisition dates**: Critical for FIFO calculation
3. **Track fees separately**: Include transaction fees in cost basis
4. **Note transaction IDs**: Keep platform transaction references

### Regular Reporting

1. **Generate monthly summaries**: Track your position throughout the year
2. **Review quarterly**: Check for any discrepancies
3. **Annual tax report**: Generate before filing deadline (June 30)

### Modelo 720 Compliance

Check if reporting is required:

```bash
# Review current portfolio value
python -m crypto_db.cli crypto balance

# Get current prices
python -m crypto_db.cli crypto price BTC
python -m crypto_db.cli crypto price ETH
```

If total holdings exceed €50,000, Modelo 720 filing is required by March 31.

## Common Scenarios

### Staking Rewards

Staking rewards are considered income at the moment they are received:
- Record as `reward` transaction type
- Use market price at time of receipt
- Subject to income tax, not just capital gains

### Transfers Between Platforms

Transfers don't trigger tax events:
- Use `transfer_out` for outgoing transfers
- Use `transfer_in` for incoming transfers
- No gain/loss calculation needed

### Cryptocurrency-to-Cryptocurrency Trades

In Spain, crypto-to-crypto trades are taxable events:
- Record as two transactions: SELL old crypto, BUY new crypto
- Calculate gains/losses on the SELL
- New crypto gets new cost basis from BUY

## Important Notes

1. **Keep EUR values**: All transactions must have EUR values for tax purposes
2. **Real-time prices**: Use actual exchange rates at transaction time
3. **Documentation**: Keep all supporting documents for 4 years
4. **Professional advice**: Consult with a tax professional for complex situations

## Filing Deadlines

- **Modelo 100 (IRPF)**: April 11 - June 30
- **Modelo 720**: January 1 - March 31 (if required)

## Resources

- [Agencia Tributaria](https://www.agenciatributaria.es/)
- Spanish Tax Agency official website for current regulations
