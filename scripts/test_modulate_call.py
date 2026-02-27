#!/usr/bin/env python3
"""
Test script for Modulate AI voice calling integration.

This script makes a single test call to verify the Modulate API integration.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.voice_dispatch_agent import VoiceDispatchAgent
from agents.driver_context_agent import DriverContextAgent
from models import OrderRequest, Location, VehicleType, TimeWindow, CustomerInfo, RankingScore
from datetime import datetime, timedelta
from config import settings
import structlog

logger = structlog.get_logger()


async def test_modulate_call():
    """Test a single Modulate voice call"""
    
    print("\n" + "="*60)
    print("🐆 CHEETAH EXPRESS - MODULATE AI CALL TEST")
    print("="*60 + "\n")
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Modulate Base URL: {settings.modulate_base_url}")
    print(f"   API Key: {'✓ Set' if settings.modulate_api_key else '✗ Missing'}")
    print(f"   Mock Mode: {settings.use_mock_data}")
    
    if settings.use_mock_data:
        print("\n⚠️  WARNING: USE_MOCK_DATA is true!")
        print("   Set USE_MOCK_DATA=false in .env to test real calls")
        print("   Exiting...\n")
        return
    
    if not settings.modulate_api_key:
        print("\n❌ ERROR: MODULATE_API_KEY not set in .env")
        print("   Please add your Modulate API key and try again\n")
        return
    
    print("\n✅ Configuration looks good!\n")
    
    # Get test driver
    print("👤 Fetching test driver...")
    driver_agent = DriverContextAgent()
    drivers = await driver_agent.get_active_drivers()
    
    if not drivers:
        print("❌ No drivers available for testing")
        return
    
    test_driver = drivers[0]  # Use DRV001
    print(f"   Driver: {test_driver.name} ({test_driver.driver_id})")
    print(f"   Phone: {test_driver.phone}")
    print(f"   Location: {test_driver.current_location.address}\n")
    
    # Create test order
    print("📦 Creating test order...")
    test_order = OrderRequest(
        order_id="TEST001",
        pickup=Location(
            address="123 Market St, San Francisco, CA 94103",
            latitude=37.7749,
            longitude=-122.4194
        ),
        dropoff=Location(
            address="456 Mission St, San Francisco, CA 94105",
            latitude=37.7849,
            longitude=-122.4094
        ),
        time_window=TimeWindow(
            start=datetime.now() + timedelta(hours=1),
            end=datetime.now() + timedelta(hours=3)
        ),
        vehicle_type=VehicleType.SEDAN,
        customer_info=CustomerInfo(
            name="Test Customer",
            phone="+1-555-0000",
            email="test@example.com"
        ),
        special_instructions="This is a test call from Cheetah Express",
        priority=5
    )
    print(f"   Order ID: {test_order.order_id}")
    print(f"   Pickup: {test_order.pickup.address}")
    print(f"   Dropoff: {test_order.dropoff.address}\n")
    
    # Create test ranking
    test_ranking = RankingScore(
        driver_id=test_driver.driver_id,
        score=95.5,
        eta_to_pickup_minutes=8.5,
        total_trip_time_minutes=25.0,
        vehicle_match=True,
        license_expiry_buffer_days=120,
        remaining_km_budget=180.0,
        reasoning="Test call - highest ranked driver"
    )
    
    # Show call script
    voice_agent = VoiceDispatchAgent()
    call_script = voice_agent._generate_call_script(test_driver, test_order, test_ranking)
    
    print("📞 Call Script Preview:")
    print("-" * 60)
    print(call_script)
    print("-" * 60 + "\n")
    
    # Confirm before calling
    print("⚠️  IMPORTANT: This will make a REAL phone call!")
    print(f"   Phone number: {test_driver.phone}")
    print(f"   Cost: ~$0.05-$0.15 per call\n")
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Test cancelled by user\n")
        return
    
    print("\n📞 Making call to Modulate API...")
    print("   (This may take 30-60 seconds...)\n")
    
    # Make the call
    try:
        result = await voice_agent._call_driver(test_driver, test_order, test_ranking)
        
        print("\n" + "="*60)
        print("📊 CALL RESULT")
        print("="*60)
        print(f"   Driver ID: {result.driver_id}")
        print(f"   Outcome: {result.outcome.value}")
        print(f"   Sentiment Score: {result.sentiment_score}")
        print(f"   Decline Reason: {result.decline_reason or 'N/A'}")
        print(f"   Call Duration: {result.call_duration_seconds}s")
        
        if result.transcript:
            print(f"\n   Transcript:")
            print(f"   {result.transcript}")
        
        print("="*60 + "\n")
        
        if result.outcome.value == "accepted":
            print("✅ SUCCESS: Driver accepted the assignment!")
        elif result.outcome.value == "declined":
            print("⚠️  Driver declined the assignment")
        elif result.outcome.value == "no_answer":
            print("⚠️  No answer from driver")
        else:
            print("❌ Call failed")
        
        print("\n💡 Next Steps:")
        print("   1. Check your phone for the call")
        print("   2. Verify the outcome matches what you said")
        print("   3. Check backend logs for detailed info")
        print("   4. Query Neo4j to see logged call data\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"   Check your Modulate API key and configuration\n")
        logger.error("Test call failed", error=str(e), exc_info=True)


if __name__ == "__main__":
    print("\n🚀 Starting Modulate AI test...\n")
    asyncio.run(test_modulate_call())
    print("✅ Test complete!\n")
