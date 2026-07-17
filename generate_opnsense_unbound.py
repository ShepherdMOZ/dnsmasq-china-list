#!/usr/bin/env python3
import argparse
import os
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate OPNsense Unbound DNS configuration subset from accelerated-domains.china.conf based on an allow list."
    )
    parser.add_argument(
        "--selected",
        default="selected-domains.txt",
        help="Path to the allow list hostname/domain file (default: selected-domains.txt)"
    )
    parser.add_argument(
        "--china",
        default="accelerated-domains.china.conf",
        help="Path to the dnsmasq accelerated domains config file (default: accelerated-domains.china.conf)"
    )
    parser.add_argument(
        "--output",
        default="selected-domains.unbound.conf",
        help="Path to save the generated Unbound configuration (default: selected-domains.unbound.conf)"
    )
    parser.add_argument(
        "--dns",
        default="223.5.5.5",
        help="DNS forwarding server IP address (default: 223.5.5.5)"
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable automatic subdomain de-duplication"
    )
    return parser.parse_args()

def load_accelerated_domains(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Accelerated domains file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    
    domains = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # dnsmasq format: server=/domain/114.114.114.114
            if line.startswith('server=/') and '/' in line[8:]:
                parts = line.split('/')
                if len(parts) >= 3:
                    domains.add(parts[1].lower())
    return domains

def load_selected_domains(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Selected domains file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
        
    selected = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            domain = line.lower()
            if domain.endswith('.'):
                domain = domain[:-1]
            selected.append(domain)
    return selected

def is_accelerated(domain, accelerated_set):
    parts = domain.split('.')
    for i in range(len(parts)):
        suffix = '.'.join(parts[i:])
        if suffix in accelerated_set:
            return True
    return False

def deduplicate_domains(domains_set):
    # domains_set is a set of lowercase domains
    sorted_domains = sorted(list(domains_set), key=len)
    unique_domains = []
    for d in sorted_domains:
        parts = d.split('.')
        has_parent = False
        for i in range(1, len(parts)):
            parent = '.'.join(parts[i:])
            if parent in domains_set:
                has_parent = True
                break
        if not has_parent:
            unique_domains.append(d)
    return unique_domains

def main():
    args = parse_args()
    
    print(f"Loading accelerated domains from {args.china}...")
    china_domains = load_accelerated_domains(args.china)
    print(f"Loaded {len(china_domains)} accelerated domains.")
    
    print(f"Loading selected domains from {args.selected}...")
    selected_domains = load_selected_domains(args.selected)
    print(f"Loaded {len(selected_domains)} selected domains/hostnames.")
    
    matched_domains = set()
    for d in selected_domains:
        if is_accelerated(d, china_domains):
            matched_domains.add(d)
            
    print(f"Matched {len(matched_domains)} domains out of {len(selected_domains)} to China acceleration list.")
    
    if not args.no_dedup:
        print("Deduplicating subdomains...")
        final_domains = deduplicate_domains(matched_domains)
        print(f"Reduced to {len(final_domains)} unique domains after deduplication.")
    else:
        final_domains = sorted(list(matched_domains))
        
    print(f"Writing Unbound configuration to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        # Write headers or comments if helpful
        f.write("# Generated OPNsense Unbound DNS config subset\n")
        f.write(f"# Based on {args.selected} and {args.china}\n\n")
        
        for d in final_domains:
            f.write("forward-zone:\n")
            f.write(f'  name: "{d}."\n')
            f.write(f"  forward-addr: {args.dns}\n\n")
            
    print("Done!")

if __name__ == "__main__":
    main()
