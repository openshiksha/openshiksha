import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { Button } from '@/shared/ui';
import { useT, type Translate } from '@/shared/i18n';
import type { ClassroomInviteCode } from '@/types/index';

const fetchClassroomCodes = async (): Promise<ClassroomInviteCode[]> => {
  const res = await apiClient.get<ClassroomInviteCode[]>('/users/me/classroom-code/');
  return res.data;
};

const generateCode = async (classroomId: number): Promise<ClassroomInviteCode> => {
  const res = await apiClient.post<ClassroomInviteCode>('/users/me/classroom-code/', {
    classroom_id: classroomId,
  });
  return res.data;
};

interface Props {
  classroomId: number;
  classroomName: string;
}

const formatExpiry = (
  expiresAt: string | null,
  t: Translate,
): { text: string; urgent: boolean } => {
  if (!expiresAt) return { text: t('classCode.noExpiry'), urgent: false };
  const expires = new Date(expiresAt).getTime();
  const now = Date.now();
  const diffMs = expires - now;
  if (diffMs <= 0) return { text: t('classCode.expired'), urgent: true };
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  if (hours < 48) {
    return {
      text: hours <= 1 ? t('classCode.expiresLtHour') : t('classCode.expiresHours', { hours }),
      urgent: true,
    };
  }
  const days = Math.floor(hours / 24);
  return { text: t('classCode.expiresDays', { days }), urgent: false };
};

export const ClassroomCodeWidget = ({ classroomId, classroomName }: Props) => {
  const t = useT();
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState<'code' | 'link' | null>(null);
  const [confirmRegenerate, setConfirmRegenerate] = useState(false);

  const { data: codes } = useQuery<ClassroomInviteCode[]>({
    queryKey: ['classroom-codes'],
    queryFn: fetchClassroomCodes,
  });

  const generateMutation = useMutation({
    mutationFn: () => generateCode(classroomId),
    onSuccess: () => {
      setConfirmRegenerate(false);
      queryClient.invalidateQueries({ queryKey: ['classroom-codes'] });
    },
  });

  const myCode = codes?.find((c) => c.classroom_id === classroomId);

  const shareLink = myCode
    ? `${window.location.origin}/register/school?code=${encodeURIComponent(myCode.code)}`
    : '';

  const handleCopy = (value: string, which: 'code' | 'link') => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(which);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  const expiry = myCode ? formatExpiry(myCode.expires_at, t) : null;

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
        {t('classCode.heading')}
      </p>
      {myCode ? (
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <code
              className="rounded-lg bg-brand-50 px-3 py-1.5 font-mono text-sm font-bold tracking-widest text-brand-800 ring-1 ring-brand-100"
              data-testid="join-code"
            >
              {myCode.code}
            </code>
            <Button variant="ghost" size="sm" onClick={() => handleCopy(myCode.code, 'code')}>
              {copied === 'code' ? t('classCode.copied') : t('classCode.copyCode')}
            </Button>
            {expiry && (
              <span
                className={`text-xs ${expiry.urgent ? 'font-semibold text-rose-600' : 'text-ink-500'}`}
                data-testid="join-code-expiry"
              >
                {expiry.text}
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              readOnly
              value={shareLink}
              data-testid="join-code-link"
              className="min-w-0 flex-1 rounded-lg border border-ink-200 bg-paper px-2 py-1 font-mono text-xs text-ink-700"
              onFocus={(e) => e.currentTarget.select()}
            />
            <Button variant="ghost" size="sm" onClick={() => handleCopy(shareLink, 'link')}>
              {copied === 'link' ? t('classCode.copied') : t('classCode.copyLink')}
            </Button>
          </div>
          {confirmRegenerate ? (
            <div
              className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-900"
              role="alertdialog"
              aria-label={t('classCode.regenConfirmAria')}
            >
              <p className="mb-2">
                {t('classCode.regenWarning')}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="brand"
                  size="sm"
                  onClick={() => generateMutation.mutate()}
                  disabled={generateMutation.isPending}
                >
                  {generateMutation.isPending ? '…' : t('classCode.yesRegenerate')}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmRegenerate(false)}
                  disabled={generateMutation.isPending}
                >
                  {t('common.cancel')}
                </Button>
              </div>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setConfirmRegenerate(true)}
              title={t('classCode.regenerateTitle', { classroom: classroomName })}
            >
              {t('classCode.regenerate')}
            </Button>
          )}
        </div>
      ) : (
        <Button
          variant="brand"
          size="sm"
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
        >
          {generateMutation.isPending ? t('classCode.generating') : t('classCode.generate')}
        </Button>
      )}
    </div>
  );
};
