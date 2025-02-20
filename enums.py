from enum import Enum

class Payments(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

    def __str__(self):
        return str(self.value)

class InterestRate(Enum):
    RATE_1 = 1.0
    RATE_1_5 = 1.5
    RATE_2 = 2.0
    RATE_2_5 = 2.5
    RATE_3 = 3.0  # Ensure consistency in float values

    def __str__(self):
        return str(self.value)

class BidStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

    def __str__(self):
        return self.value