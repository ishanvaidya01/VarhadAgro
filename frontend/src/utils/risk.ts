export function getRiskColor(prob: number | null): string {
  if (prob === null || prob === undefined) return '#E8E3D7';
  if (prob < 0.20) return '#FFFFD4';
  if (prob < 0.35) return '#FED98E';
  if (prob < 0.50) return '#FE9929';
  if (prob < 0.70) return '#D95F0E';
  return '#993404';
}

export function getRiskLabel(prob: number | null): string {
  if (prob === null || prob === undefined) return 'No data';
  if (prob < 0.20) return 'Low (<20%)';
  if (prob < 0.35) return 'Moderate (20-35%)';
  if (prob < 0.50) return 'Elevated (35-50%)';
  if (prob < 0.70) return 'High (50-70%)';
  return 'Severe (>70%)';
}
