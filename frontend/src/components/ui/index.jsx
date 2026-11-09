// shadcn/ui-style primitives (Radix + Tailwind), kept in one file
import * as React from 'react'
import { cva } from 'class-variance-authority'
import * as SliderPrimitive from '@radix-ui/react-slider'
import * as SwitchPrimitive from '@radix-ui/react-switch'
import * as TabsPrimitive from '@radix-ui/react-tabs'
import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group'
import * as SelectPrimitive from '@radix-ui/react-select'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { Check, ChevronDown, X } from 'lucide-react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-40 cursor-pointer select-none',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-muted text-foreground hover:bg-accent border',
        ghost: 'hover:bg-accent text-foreground',
        outline: 'border bg-transparent hover:bg-accent',
        destructive: 'bg-destructive/15 text-destructive hover:bg-destructive/25',
        success: 'bg-success/15 text-success hover:bg-success/25',
      },
      size: { default: 'h-9 px-4', sm: 'h-8 px-3 text-xs', xs: 'h-7 px-2 text-xs', icon: 'h-8 w-8', lg: 'h-11 px-6 text-base' },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)
export const Button = React.forwardRef(({ className, variant, size, ...p }, ref) => (
  <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...p} />
))

export const Badge = ({ className, tone = 'muted', ...p }) => (
  <span
    className={cn(
      'inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
      tone === 'muted' && 'bg-muted text-muted-foreground',
      tone === 'new' && 'bg-success/15 text-success',
      tone === 'blue' && 'bg-primary/20 text-primary',
      tone === 'warn' && 'bg-yellow-500/15 text-yellow-400',
      className,
    )}
    {...p}
  />
)

export const Slider = ({ className, ...p }) => (
  <SliderPrimitive.Root className={cn('relative flex h-5 w-full touch-none select-none items-center', className)} {...p}>
    <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-muted">
      <SliderPrimitive.Range className="absolute h-full bg-primary" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-4 w-4 rounded-full border-2 border-primary bg-white shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
  </SliderPrimitive.Root>
)

export const Switch = ({ className, ...p }) => (
  <SwitchPrimitive.Root
    className={cn('peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full bg-muted transition-colors data-[state=checked]:bg-primary border', className)}
    {...p}
  >
    <SwitchPrimitive.Thumb className="pointer-events-none block h-4 w-4 translate-x-0.5 rounded-full bg-white shadow transition-transform data-[state=checked]:translate-x-[18px]" />
  </SwitchPrimitive.Root>
)

export const Tabs = TabsPrimitive.Root
export const TabsList = ({ className, ...p }) => (
  <TabsPrimitive.List className={cn('inline-flex h-9 w-full items-center rounded-lg bg-muted p-1', className)} {...p} />
)
export const TabsTrigger = ({ className, ...p }) => (
  <TabsPrimitive.Trigger
    className={cn('inline-flex flex-1 items-center justify-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground transition-all cursor-pointer data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow', className)}
    {...p}
  />
)
export const TabsContent = ({ className, ...p }) => <TabsPrimitive.Content className={cn('outline-none', className)} {...p} />

export const ToggleGroup = ({ className, ...p }) => (
  <ToggleGroupPrimitive.Root type="single" className={cn('inline-flex w-full rounded-lg bg-muted p-1', className)} {...p} />
)
export const ToggleItem = ({ className, ...p }) => (
  <ToggleGroupPrimitive.Item
    className={cn('flex-1 rounded-md px-2 py-1.5 text-xs font-medium text-muted-foreground cursor-pointer transition-colors hover:text-foreground data-[state=on]:bg-card data-[state=on]:text-foreground data-[state=on]:shadow', className)}
    {...p}
  />
)

export const Select = ({ value, onValueChange, options, className, placeholder }) => (
  <SelectPrimitive.Root value={value} onValueChange={onValueChange}>
    <SelectPrimitive.Trigger
      className={cn('flex h-9 w-full items-center justify-between rounded-lg border bg-muted px-3 text-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring', className)}
    >
      <SelectPrimitive.Value placeholder={placeholder} />
      <ChevronDown className="h-4 w-4 opacity-60" />
    </SelectPrimitive.Trigger>
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content position="popper" sideOffset={4} className="z-[100] max-h-72 min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-lg border bg-card text-sm shadow-xl">
        <SelectPrimitive.Viewport className="p-1">
          {options.map((o) => (
            <SelectPrimitive.Item
              key={o.value}
              value={o.value}
              className="relative flex cursor-pointer select-none items-center rounded-md py-1.5 pl-7 pr-3 outline-none data-[highlighted]:bg-accent"
            >
              <SelectPrimitive.ItemIndicator className="absolute left-2"><Check className="h-3.5 w-3.5" /></SelectPrimitive.ItemIndicator>
              <SelectPrimitive.ItemText>{o.label}</SelectPrimitive.ItemText>
            </SelectPrimitive.Item>
          ))}
        </SelectPrimitive.Viewport>
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  </SelectPrimitive.Root>
)

export const Dialog = DialogPrimitive.Root
export const DialogContent = ({ className, children, title, description, ...p }) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/70" />
    <DialogPrimitive.Content
      className={cn('fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-[min(920px,94vw)] -translate-x-1/2 -translate-y-1/2 overflow-auto rounded-xl border bg-card p-5 shadow-2xl outline-none', className)}
      {...p}
    >
      <DialogPrimitive.Title className="text-base font-semibold">{title}</DialogPrimitive.Title>
      {description && <DialogPrimitive.Description className="mt-1 text-xs text-muted-foreground">{description}</DialogPrimitive.Description>}
      <div className="mt-4">{children}</div>
      <DialogPrimitive.Close className="absolute right-3 top-3 rounded-md p-1 text-muted-foreground hover:bg-accent cursor-pointer"><X className="h-4 w-4" /></DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
)

export const Progress = ({ value = 0, className, indeterminate }) => (
  <div className={cn('h-2 w-full overflow-hidden rounded-full bg-muted', className)}>
    <div
      className={cn('h-full rounded-full bg-primary transition-all duration-300', indeterminate && 'animate-pulse')}
      style={{ width: Math.max(3, Math.min(100, value)) + '%' }}
    />
  </div>
)

export const Label = ({ className, ...p }) => <label className={cn('text-xs font-medium text-muted-foreground', className)} {...p} />

export const Section = ({ title, hint, children, className }) => (
  <div className={cn('rounded-xl border bg-card/60 p-3', className)}>
    <div className="mb-2.5">
      <div className="text-sm font-semibold">{title}</div>
      {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
    </div>
    <div className="space-y-3">{children}</div>
  </div>
)
