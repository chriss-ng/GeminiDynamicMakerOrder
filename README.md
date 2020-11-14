# GeminiDynamicMakerOrder

A simple bot that makes a market order without paying the taker fee. It instead pays the maker fee. 

This is achieved by constantly creating and updating MakerOrCancel (MOC) orders every 5 seconds (by default). 
