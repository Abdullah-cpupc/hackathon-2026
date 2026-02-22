declare module '@radix-ui/react-accordion' {
  import * as React from 'react'
  export type ForwardRefComp = React.ForwardRefExoticComponent<any & React.RefAttributes<any>>
  export const Root: ForwardRefComp
  export const Item: ForwardRefComp
  export const Header: ForwardRefComp
  export const Trigger: ForwardRefComp
  export const Content: ForwardRefComp
}
