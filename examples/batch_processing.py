"""Batch processing examples for ValidKit Python SDK"""

import asyncio
import csv
import json
from pathlib import Path
from typing import List, Dict
from validkit import AsyncValidKit, BatchJob, CompactResult


async def large_batch_example():
    """Example: Process a large batch of emails efficiently"""
    print("=== Large Batch Processing ===")
    
    # Generate 10,000 test emails
    emails = []
    for i in range(10000):
        domain = ["gmail.com", "yahoo.com", "outlook.com", "example.com"][i % 4]
        emails.append(f"user{i}@{domain}")
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        print(f"Verifying {len(emails)} emails...")
        
        # Progress tracking
        start_time = asyncio.get_event_loop().time()
        
        async def progress_callback(processed, total):
            elapsed = asyncio.get_event_loop().time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed) / rate if rate > 0 else 0
            
            print(f"Progress: {processed:,}/{total:,} "
                  f"({processed/total*100:.1f}%) "
                  f"Rate: {rate:.0f}/s "
                  f"ETA: {eta:.0f}s")
        
        results = await client.verify_batch(
            emails,
            chunk_size=1000,
            progress_callback=progress_callback
        )
        
        # Analyze results
        valid = sum(1 for r in results.values() if r.v)
        disposable = sum(1 for r in results.values() if r.v and r.d)
        invalid = len(results) - valid
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        print(f"\nCompleted in {elapsed:.1f} seconds")
        print(f"Valid: {valid:,} ({valid/len(emails)*100:.1f}%)")
        print(f"Invalid: {invalid:,} ({invalid/len(emails)*100:.1f}%)")
        print(f"Disposable: {disposable:,} ({disposable/len(emails)*100:.1f}%)")
        print(f"Rate: {len(emails)/elapsed:.0f} emails/second")


async def csv_processing_example():
    """Example: Process emails from CSV file"""
    print("\n=== CSV File Processing ===")
    
    # Create sample CSV file
    csv_file = Path("emails.csv")
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["email", "name", "company"])
        writer.writerow(["john.doe@gmail.com", "John Doe", "Acme Corp"])
        writer.writerow(["jane@tempmail.com", "Jane Smith", "Tech Inc"])
        writer.writerow(["invalid.email", "Invalid User", "Bad Corp"])
        writer.writerow(["test@example.com", "Test User", "Example LLC"])
    
    # Read and process emails
    emails = []
    email_metadata = {}
    
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row["email"]
            emails.append(email)
            email_metadata[email] = row
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        print(f"Processing {len(emails)} emails from CSV...")
        
        results = await client.verify_batch(emails)
        
        # Create output CSV with verification results
        output_file = Path("emails_verified.csv")
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "name", "company", "valid", "disposable", "reason"])
            
            for email, result in results.items():
                metadata = email_metadata[email]
                writer.writerow([
                    email,
                    metadata["name"],
                    metadata["company"],
                    "Yes" if result.v else "No",
                    "Yes" if result.d else "No",
                    result.r or ""
                ])
        
        print(f"Results saved to {output_file}")
    
    # Cleanup
    csv_file.unlink()
    output_file.unlink()


async def async_webhook_example():
    """Example: Process large batch asynchronously with webhook"""
    print("\n=== Async Batch with Webhook ===")
    
    # Generate large email list
    emails = [f"user{i}@example.com" for i in range(5000)]
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        # Start async job
        job = await client.verify_batch_async(
            emails=emails,
            webhook_url="https://your-app.com/webhooks/validkit",
            webhook_headers={
                "Authorization": "Bearer your_webhook_token",
                "X-Custom-Header": "custom_value"
            }
        )
        
        print(f"Batch job started: {job.id}")
        print(f"Status URL: {job.status_url}")
        print(f"Total emails: {job.total_emails}")
        
        # Poll for status
        while not job.is_complete:
            await asyncio.sleep(5)
            job = await client.get_batch_status(job.id)
            
            print(f"Status: {job.status} "
                  f"Progress: {job.processed}/{job.total_emails} "
                  f"({job.progress_percentage:.1f}%)")
        
        print(f"\nJob completed!")
        print(f"Valid: {job.valid}")
        print(f"Invalid: {job.invalid}")
        print(f"Processing time: {(job.completed_at - job.created_at).total_seconds():.1f}s")


async def domain_grouping_example():
    """Example: Group results by domain"""
    print("\n=== Domain Analysis ===")
    
    emails = [
        "user1@gmail.com",
        "user2@gmail.com",
        "user3@yahoo.com",
        "user4@outlook.com",
        "user5@tempmail.com",
        "user6@guerrillamail.com",
        "user7@company.com",
        "user8@gmail.com",
        "invalid@",
        "notanemail"
    ]
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        results = await client.verify_batch(emails)
        
        # Group by domain
        domain_stats: Dict[str, Dict[str, int]] = {}
        
        for email, result in results.items():
            if '@' in email:
                domain = email.split('@')[1]
            else:
                domain = 'invalid'
            
            if domain not in domain_stats:
                domain_stats[domain] = {
                    'total': 0,
                    'valid': 0,
                    'disposable': 0
                }
            
            domain_stats[domain]['total'] += 1
            if result.v:
                domain_stats[domain]['valid'] += 1
            if result.d:
                domain_stats[domain]['disposable'] += 1
        
        # Display results
        print("Domain Statistics:")
        print("-" * 50)
        print(f"{'Domain':<20} {'Total':>8} {'Valid':>8} {'Disposable':>12}")
        print("-" * 50)
        
        for domain, stats in sorted(domain_stats.items()):
            print(f"{domain:<20} {stats['total']:>8} {stats['valid']:>8} {stats['disposable']:>12}")


async def retry_failed_example():
    """Example: Retry failed verifications"""
    print("\n=== Retry Failed Verifications ===")
    
    emails = [
        "good@gmail.com",
        "bad@nonexistent-domain-12345.com",
        "timeout@slow-server.com",
        "another@gmail.com"
    ]
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        # First attempt
        print("First verification attempt...")
        results = await client.verify_batch(emails)
        
        # Identify failed verifications
        failed_emails = []
        for email, result in results.items():
            if not result.v and result.r and "timeout" in result.r.lower():
                failed_emails.append(email)
        
        if failed_emails:
            print(f"\nRetrying {len(failed_emails)} failed verifications...")
            
            # Retry with longer timeout
            retry_config = client.config
            retry_config.timeout = 60  # Increase timeout
            
            retry_results = await client.verify_batch(failed_emails)
            
            # Update original results
            results.update(retry_results)
            
            print("Retry complete!")
        
        # Final results
        valid = sum(1 for r in results.values() if r.v)
        print(f"\nFinal results: {valid}/{len(emails)} valid")


async def export_formats_example():
    """Example: Export results in different formats"""
    print("\n=== Export Formats ===")
    
    emails = ["user1@gmail.com", "user2@yahoo.com", "disposable@tempmail.com"]
    
    async with AsyncValidKit(api_key="your_api_key") as client:
        results = await client.verify_batch(emails)
        
        # Export as JSON
        json_data = {
            "timestamp": asyncio.get_event_loop().time(),
            "total": len(results),
            "results": {
                email: {
                    "valid": result.v,
                    "disposable": result.d,
                    "reason": result.r
                }
                for email, result in results.items()
            }
        }
        
        json_file = Path("results.json")
        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"Exported to {json_file}")
        
        # Export as line-delimited JSON (for streaming)
        ndjson_file = Path("results.ndjson")
        with open(ndjson_file, "w") as f:
            for email, result in results.items():
                line = json.dumps({
                    "email": email,
                    "valid": result.v,
                    "disposable": result.d,
                    "reason": result.r
                })
                f.write(line + "\n")
        print(f"Exported to {ndjson_file}")
        
        # Export summary
        summary_file = Path("summary.txt")
        with open(summary_file, "w") as f:
            valid = sum(1 for r in results.values() if r.v)
            disposable = sum(1 for r in results.values() if r.d)
            
            f.write(f"Email Verification Summary\n")
            f.write(f"========================\n")
            f.write(f"Total emails: {len(results)}\n")
            f.write(f"Valid: {valid} ({valid/len(results)*100:.1f}%)\n")
            f.write(f"Invalid: {len(results)-valid} ({(len(results)-valid)/len(results)*100:.1f}%)\n")
            f.write(f"Disposable: {disposable} ({disposable/len(results)*100:.1f}%)\n")
        print(f"Exported to {summary_file}")
        
        # Cleanup
        json_file.unlink()
        ndjson_file.unlink()
        summary_file.unlink()


async def main():
    """Run all batch processing examples"""
    # Note: Replace "your_api_key" with actual API key
    
    await large_batch_example()
    await csv_processing_example()
    await async_webhook_example()
    await domain_grouping_example()
    await retry_failed_example()
    await export_formats_example()


if __name__ == "__main__":
    asyncio.run(main())