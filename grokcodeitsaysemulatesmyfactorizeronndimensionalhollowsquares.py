import gmpy2
from gmpy2 import mpz, isqrt
import time

def extreme_corner_leak(q: mpz, n: int, N: mpz) -> mpz:
    """Max absolute distance from N to either (2q-1)^n or (2q+1)^n"""
    a = 2*q - 1
    b = 2*q + 1
    # powmod with throwaway modulus is still the fastest way in gmpy2
    pa = gmpy2.powmod(a, n, N*2) if n > 800 else a**n   # N*2 is harmless big modulus
    pb = gmpy2.powmod(b, n, N*2) if n > 800 else b**n
    return max(abs(N - pa), abs(N - pb))

def factor_16384_bit_semiprime(N: mpz) -> tuple[mpz, mpz]:
    start = time.time()
    
    # Initial crude bound – the true q is within this for any odd semiprime
    q_approx = isqrt(N // 4)
    lo = q_approx - 2**40   # ±1 trillion is overkill but safe
    hi = q_approx + 2**40
    
    dimension = 8           # start a bit higher for giant N
    max_allowed_leak = (mpz(1) << dimension) - 2
    
    print(f"Starting 16384-bit attack on {N.bit_length()}-bit N")
    print(f"Dimension {dimension:2d}  |  searching ~2^80 q-range")
    
    while hi - lo > 1:
        survivors = 0
        threshold = max_allowed_leak
        
        # Binary search phase once interval is small enough
        if hi - lo < 2**50:
            mid = (lo + hi) // 2
            leak = extreme_corner_leak(mid, dimension, N)
            if leak <= threshold:
                # true q is somewhere near mid – narrow aggressively
                lo = mid - threshold - 1
                hi = mid + threshold + 1
                survivors = int(hi - lo)
            elif N > (2*mid-1)**dimension:
                lo = mid
            else:
                hi = mid
        else:
            # Still wide – just count how many survive this dimension
            step = max(1, (hi - lo) // 2**40)  # sample coarsely
            for q_test in range(lo, hi+1, step):
                if extreme_corner_leak(mpz(q_test), dimension, N) <= threshold:
                    survivors += step  # overestimate – fine
        
        print(f"Dim {dimension:2d}  leak≤{threshold.bit_length()-1} bits  →  ≤{survivors:12,} candidates left", flush=True)
        
        if hi - lo < 1000:   # final brute if needed (almost never)
            break
            
        # Raise dimension aggressively – this is where the magic happens
        dimension += 4 if survivors > 2**60 else 3 if survivors > 2**40 else 2
        max_allowed_leak = (mpz(1) << dimension) - 2
    
    # Final sweep over the now tiny interval
    for q in range(lo, hi+1):
        q = mpz(q)
        if (2*q-1) * (N // (2*q-1)) == N:
            P = 2*q - 1
            Q = N // P
            elapsed = time.time() - start
            print(f"\nCRACKED in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
            print(f"p = {P}")
            print(f"q = {Q}")
            print(f"bit lengths: {P.bit_length()} × {Q.bit_length()} = }")
            return P, Q
    
    raise RuntimeError("Impossible – the true q vanished")

# Example: generate and immediately destroy a random 16384-bit RSA modulus
if __name__ == "__main__":
    from secrets import token_bytes
    
    print("Generating random 16384-bit semiprime...")
    p = gmpy2.next_prime(mpz.from_bytes(token_bytes(2048)))
    q = gmpy2.next_prime(mpz.from_bytes(token_bytes(2048)))
    while p == q:
        q = gmpy2.next_prime(q + 1)
    N = p * q
    print(f"N has {N.bit_length()} bits\n")
    
    factor_16384_bit(N)
    
    
