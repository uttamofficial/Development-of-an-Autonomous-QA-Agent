# Product Specifications - E-Shop Checkout

## Overview
This document outlines the feature specifications for the E-Shop checkout system.

## Discount Codes

### Valid Discount Codes
- **SAVE10**: Applies a 10% discount to the total order amount
- **SAVE15**: Applies a 15% discount to the total order amount
- **SAVE20**: Applies a 20% discount to the total order amount
- **WELCOME**: Applies a 15% discount for new customers

### Discount Code Rules
- Discount codes are case-sensitive
- Only one discount code can be applied per order
- Discount codes cannot be combined
- Discount is applied to the subtotal before shipping costs
- Invalid discount codes should display an error message
- Empty discount code field should not apply any discount

## Shipping Methods

### Standard Shipping
- **Cost**: Free (no additional charge)
- **Delivery Time**: 5-7 business days
- **Availability**: Available for all orders

### Express Shipping
- **Cost**: $10.00 flat rate
- **Delivery Time**: 2-3 business days
- **Availability**: Available for all orders

### Shipping Rules
- Shipping cost is added to the order total after discount is applied
- Customer must select a shipping method before checkout
- Standard shipping is selected by default
- Shipping method selection is required

## Payment Methods

### Credit Card
- Accepts all major credit cards (Visa, MasterCard, American Express)
- Payment is processed immediately upon order submission
- Customer must provide card details (handled by payment gateway)

### PayPal
- Customer is redirected to PayPal for authentication
- Payment is processed through PayPal's secure system
- Customer must have a valid PayPal account

### Payment Rules
- Customer must select a payment method before checkout
- Credit Card is selected by default
- Payment method selection is required
- Payment processing occurs after form validation passes

## Pricing Rules

### Product Pricing
- All prices are displayed in USD
- Prices are fixed and do not change during checkout
- Quantity changes update the total price automatically
- Cart total is calculated as: (item price × quantity) for all items

### Order Total Calculation
1. Calculate subtotal: Sum of (item price × quantity) for all cart items
2. Apply discount (if valid code entered): subtotal × (1 - discount_percentage/100)
3. Add shipping cost: discounted_subtotal + shipping_cost
4. Final total = discounted_subtotal + shipping_cost

### Example Calculation
- Item 1: $79.99 × 2 = $159.98
- Item 2: $199.99 × 1 = $199.99
- Subtotal: $359.97
- Discount (SAVE15): $359.97 × 0.85 = $305.97
- Express Shipping: $10.00
- **Final Total: $315.97**

## Form Validation Rules

### Required Fields
- **Full Name**: Must not be empty, minimum 2 characters
- **Email Address**: Must be a valid email format (contains @ and domain)
- **Shipping Address**: Must not be empty, minimum 10 characters

### Validation Behavior
- Fields are validated on blur (when user leaves the field)
- Invalid fields display red error messages below the input
- Form cannot be submitted until all validations pass
- Error messages are displayed inline in red text

## Cart Management

### Adding Items
- Users can add items to cart by clicking "Add to Cart" button
- Items can be added multiple times (increases quantity)
- Cart persists during the checkout session

### Updating Quantities
- Users can modify quantities using the quantity input field
- Minimum quantity is 1
- Setting quantity to 0 removes the item from cart
- Total price updates automatically when quantity changes

### Cart Requirements
- Cart must contain at least one item before checkout
- Empty cart should prevent form submission
- Cart items are displayed with name, price, quantity, and subtotal

## Success Criteria

### Successful Checkout
- All form fields are valid
- At least one item is in the cart
- Shipping method is selected
- Payment method is selected
- Upon clicking "Pay Now", a success message is displayed: "Payment Successful! 🎉"

### Error Handling
- Invalid discount codes show error message
- Invalid form fields show red error messages
- Empty cart shows alert message
- All errors are user-friendly and actionable

