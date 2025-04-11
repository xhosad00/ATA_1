#!/usr/bin/env python3
"""
Example of usage/test of Cart controller implementation.
"""

import sys
import unittest
# from cartctl.cartctl.cartctl import CartCtl
from cartctl.cartctl import CartCtl
from cartctl.cartctl import Status as CartCtlStatus
from cartctl.cart import Cart, CargoReq, CartError
from cartctl.cart import Status as CartStatus
from cartctl.jarvisenv import Jarvis

def log(msg):
    "simple logging"
    print('  %s' % msg)

# Basic functions with no asserts
def add_load(ctl: CartCtl, cargo_req: CargoReq):
    log('%d: Requesting %s at %s' % \
        (Jarvis.time(), cargo_req, cargo_req.src))
    ctl.request(cargo_req)

def on_move(cart: Cart):
    log('%d: Cart is moving %s->%s' % (Jarvis.time(), cart.pos, cart.data))

def on_load(cart: Cart, cargo_req: CargoReq):
    log('%d: Cart at %s: loading: %s' % (Jarvis.time(), cart.pos, cargo_req))
    log(cart)
    cargo_req.context = "loaded"

def on_unload(cart: Cart, cargo_req: CargoReq):
    log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), cart.pos, cargo_req))
    log(cart)
    cargo_req.context = "unloaded"

def createBasicCargo(src, dst, weight, name):
    req = CargoReq(src, dst, weight, name)
    req.onload = on_load
    req.onunload = on_unload
    return req
    
class TestCartRequests(unittest.TestCase):

    def test_happy_no_prio(self):
        "Happy-path with no priority cargo"
        print("")

        
        def on_move(cart: Cart):
            log('%d: Cart is moving %s->%s' % (Jarvis.time(), cart.pos, cart.data))
            self.assertEqual(CartStatus.MOVING, cart.status)
            self.assertFalse(cart.empty())  #during entire run, the cart should have some cargo

        def on_load(cart: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: loading: %s' % (Jarvis.time(), cart.pos, cargo_req))
            log(cart)
            self.assertFalse(cart.empty())
            self.assertEqual(None, cargo_req.context)
            cargo_req.context = "loaded"
            if cargo_req.content == 'broccoli':
                self.assertEqual('A', cart.pos)
                self.assertEqual(cargo_req.weight, cart.load_sum())
            if cargo_req.content == 'carrot':
                self.assertEqual('B', cart.pos)
            if cargo_req.content == 'daikon':
                self.assertEqual('C', cart.pos)
            if cargo_req.content == 'onion':
                self.assertEqual('C', cart.pos)

        def on_unload(cart: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), cart.pos, cargo_req))
            log(cart)
            self.assertEqual("loaded", cargo_req.context)
            cargo_req.context = "unloaded"
            if cargo_req.content == 'broccoli':
                self.assertEqual('B', cart.pos)
            if cargo_req.content == 'carrot':
                self.assertEqual('C', cart.pos)
            if cargo_req.content == 'daikon':
                self.assertEqual('A', cart.pos)
            if cargo_req.content == 'onion':
                self.assertEqual('D', cart.pos)

        def createBasicCargo(src, dst, weight, name):
            req = CargoReq(src, dst, weight, name)
            req.onload = on_load
            req.onunload = on_unload
            return req

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)
        broccoli = createBasicCargo('A', 'B', 30, 'broccoli')
        carrot = createBasicCargo('B', 'C', 100, 'carrot')
        daikon = createBasicCargo('C', 'A', 10, 'daikon')
        onion = createBasicCargo('C', 'D', 20, 'onion')

        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))
        Jarvis.plan(30, add_load, (ctl,carrot))
        Jarvis.plan(35, add_load, (ctl,daikon))
        Jarvis.plan(38, add_load, (ctl,onion))
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual('unloaded', broccoli.context)
        self.assertEqual('unloaded', carrot.context)
        self.assertEqual('unloaded', daikon.context)
        self.assertEqual('unloaded', onion.context)
        self.assertEqual(cart.pos, 'A')


    def test_happy_prio(self):
        "Happy-path with priority cargo"
        print("\n")

        def on_move(cart: Cart):
            log('%d: Cart is moving %s->%s' % (Jarvis.time(), cart.pos, cart.data))
            self.assertEqual(CartStatus.MOVING, cart.status)

        def on_load(cart: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: loading: %s' % (Jarvis.time(), cart.pos, cargo_req))
            log(cart)
            self.assertFalse(cart.empty())
            self.assertEqual(None, cargo_req.context)
            cargo_req.context = "loaded"

        def on_unload(cart: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), cart.pos, cargo_req))
            log(cart)
            cargo_req.context = "unloaded"
            if cargo_req.content == 'carrot':
                self.assertEqual('B', cart.pos)
                self.assertEqual(0, cart.load_sum()) # check that daikon wasnt loaded (Unload_Only)

        def createBasicCargo(src, dst, weight, name):
            req = CargoReq(src, dst, weight, name)
            req.onload = on_load
            req.onunload = on_unload
            return req
        
        def checkUNLOAD_ONLY(ctl :CartCtl):
            self.assertEqual(CartCtlStatus.UNLOAD_ONLY, ctl.status)

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)
        
        broccoli = createBasicCargo('B', 'D', 150, 'broccoli')
        carrot = createBasicCargo('D', 'B', 30, 'carrot')
        daikon = createBasicCargo('A', 'B', 40, 'daikon')

        Jarvis.reset_scheduler()
        Jarvis.plan(1, add_load, (ctl,broccoli))
        Jarvis.plan(2, add_load, (ctl,carrot))
        Jarvis.plan(70, add_load, (ctl,daikon))
        Jarvis.plan(90, checkUNLOAD_ONLY, (ctl,))
        Jarvis.run()

        # # Verify direct output
        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual('unloaded', broccoli.context)
        self.assertEqual('unloaded', carrot.context)
        self.assertEqual('unloaded', daikon.context)
        # self.assertEqual(cart.pos, 'D')

    def test_optimize_total_path(self):
        """Require good path optimization"""
        # optimezed path:           A->B->C->D->A  total path length=70
        # worse path (due to UCS):  A->B->A->B->C->D

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)

        broccoli = createBasicCargo('A', 'B', 20, 'broccoli')
        carrot = createBasicCargo('B', 'A', 30, 'carrot')
        daikon = createBasicCargo('B', 'D', 40, 'daikon')
        Jarvis.reset_scheduler()
        Jarvis.plan(1, add_load, (ctl,broccoli))
        Jarvis.plan(2, add_load, (ctl,carrot))
        Jarvis.plan(3, add_load, (ctl,daikon))
        Jarvis.run()
        self.assertEqual(cart.pos, 'A')

        cart = Cart(4, 150, 0)
        ctl = CartCtl(cart, Jarvis)

    def test_time_req_1s(self):
        """Test if req is processed under 1s"""
        # P-01 The system shall process a cargo transfer request within 1 second of its creation
        def req_time_check(cart: Cart, ctl: CartCtl):
            # self.assert
            print(Jarvis.time())
            self.assertTrue(cart.empty())
            self.assertEqual(len(ctl.requests), 1)

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)

        broccoli = createBasicCargo('B', 'C', 20, 'broccoli')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))
        Jarvis.plan(0.999, req_time_check, (cart, ctl))
        Jarvis.run()

        cart = Cart(4, 150, 0)
        ctl = CartCtl(cart, Jarvis)

    def test_time_pathing_1s(self):
        """Test if optimisation algorithm shall run within a time less than 1 second"""
        # P-03 The route optimisation algorithm shall run within a time less than 1 second.
        # check that te delay after load to Move is < 1s (planning under 1s)            
        time = -1
        def on_move(cart: Cart):
            log('%d: Cart is moving %s->%s' % (Jarvis.time(), cart.pos, cart.data))
            self.assertEqual(CartStatus.MOVING, cart.status)
            self.assertFalse(cart.empty())
            print (Jarvis.time(), time)
            self.assertTrue(Jarvis.time() - time < 1) # check that

        def on_load(cart: Cart, cargo_req: CargoReq):
            nonlocal time
            log('%d: Cart at %s: loading: %s' % (Jarvis.time(), cart.pos, cargo_req))
            log(cart)
            cargo_req.context = "loaded"
            time = Jarvis.time()

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)
        broccoli = createBasicCargo('A', 'B', 20, 'broccoli')
        broccoli.onload = on_load
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))
        Jarvis.run()

    def test_time_Normal_to_UO_switch(self):
        """Test if switch to UNLOAD_ONLY happens instantly after loading prio cargo"""
        # P-04 Switching the cart to unloading-only mode shall occur immediately after loading priority cargo.
        def UO_time_check(cart: Cart, ctl: CartCtl):
            self.assertEqual(CartCtlStatus.UNLOAD_ONLY, ctl.status)

        def on_load(cart: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: loading: %s' % (Jarvis.time(), cart.pos, cargo_req))
            log(cart)
            Jarvis.SCHED.enter(0, 1, UO_time_check, argument=(cart, ctl), kwargs={}) # Do the UO check as the last event in the same time (event with prio 1)

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)
        broccoli = createBasicCargo('A', 'B', 20, 'broccoli')
        broccoli.prio = True # SET BROCOLI TO PRIO CARGO
        broccoli.onload = on_load
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))        
        Jarvis.run()

    def test_time_UO_to_Normal_switch(self):
        """Test if switch to NORMAL form UO happens within 1s after unloading prio cargo"""
        # P-05 Switching back to normal mode shall occur within 1 second after unloading the last priority cargo.
        def NORMAL_time_check(ctl: CartCtl):
            self.assertEqual(CartCtlStatus.NORMAL, ctl.status)

        def on_unload(cart: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), cart.pos, cargo_req))
            log(cart)
            Jarvis.plan(1, NORMAL_time_check, (ctl,))

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)
        broccoli = createBasicCargo('A', 'B', 20, 'broccoli')
        carrot = createBasicCargo('B', 'A', 30, 'carrot')   # second item is needed, because otherwise the cart after broccoli unload will switch to IDLE
        broccoli.onunload = on_unload
        broccoli.prio = True # SET BROCOLI TO PRIO CARGO
        broccoli.onload = on_load
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))
        Jarvis.plan(1, add_load, (ctl,carrot))           
        Jarvis.run()

    def test_cart_props_slots(self):
        """test cart slot restrtictions"""
        # "C-01 The cart shall have a capacity of 1 to 4 slots"
        Cart(1, 150, 0)
        Cart(2, 150, 0)
        Cart(3, 150, 0)
        Cart(4, 150, 0)
        self.assertRaises(CartError, Cart, 0, 50, 0)
        self.assertRaises(CartError, Cart, 5, 50, 0)

        # C-03 Carts with the lowest capacity shall have at least 2 slots
        self.assertRaises(CartError, Cart, 1, 50, 0)

        # C-04 Carts with the highest capacity shall not have more than 2 slots.
        Cart(1, 500, 0)
        Cart(2, 500, 0)
        self.assertRaises(CartError, Cart, 3, 500, 0)

    def test_cart_props_weight(self):
        """test cart weight restrtictions"""
        # C-02 The cart’s maximum capacity shall correspond to its type (50kg, 150 kg, or 500 kg).
        Cart(2, 50, 0)
        Cart(2, 150, 0)
        Cart(2, 500, 0)
        # bad cart configs
        self.assertRaises(CartError, Cart, 2, 0, 0)
        self.assertRaises(CartError, Cart, 2, 1, 0)
        self.assertRaises(CartError, Cart, 2, 200, 0)
        self.assertRaises(CartError, Cart, 2, 501, 0)
        self.assertRaises(CartError, Cart, 2, 99.9, 0)

    def test_cart_props_bad_req(self):
        """test cart bad requests restrtictions"""
        # C-05 The control system shall not submit invalid requests (e.g.,cargo transfer exceeding the cart’s capacity).
        def add_load(ctl: CartCtl, cargo_req: CargoReq):
            ctl.request(cargo_req)

        def add_load_err(ctl: CartCtl, cargo_req: CargoReq):
            self.assertRaises(CartError, ctl.request, cargo_req)

        cart = Cart(2, 500, 0)
        ctl = CartCtl(cart, Jarvis)

        #ok
        broccoli = CargoReq('A', 'D', 50, 'broccoli')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))
        Jarvis.run()
        
        self.assertRaises(AssertionError, CargoReq, 'A', 'D', -1, 'bigBroccoli') #Should throw CartError
        
        # Should throw errors
        # F-10 is badly worded, needs clarification (if error is thrown in cartctl.request)
        cart = Cart(2, 500, 0)
        ctl = CartCtl(cart, Jarvis)        
        bigBroccoli = CargoReq('A', 'D', 1000, 'bigBroccoli')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load_err, (ctl,bigBroccoli))
        Jarvis.run()        

        # F-10 is badly worded, needs clarification (if error is thrown in cartctl.request or on loading)
        cart = Cart(2, 500, 1)
        cart.onmove = on_move
        broccoli1 = createBasicCargo('B', 'D', 50, 'broccoli1')
        broccoli2 = createBasicCargo('B', 'D', 50, 'broccoli2')
        broccoli3 = createBasicCargo('B', 'D', 50, 'broccoli3')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli1))
        Jarvis.plan(1, add_load, (ctl,broccoli2))
        Jarvis.plan(2, add_load_err, (ctl,broccoli3))
        Jarvis.run()
        
    

if __name__ == "__main__":
    unittest.main()
