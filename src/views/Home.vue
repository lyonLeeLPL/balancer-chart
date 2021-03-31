<template>
  <div ref="fullpage">
    <b-nav style="height:38px; z-index: 999;">
      <b-nav-item>
        <v-select
          :disabled="loading == true"
          class="select-size-sm"
          style="min-width: 400px"
          :resetOnOptionsChange="true"
          label="id"
          :filter-by="selectFilter"
          dir="ltr"
          :options="pools"
          placeholder="Search pool..."
          @input="poolChanged"
        >
          <template #option="{ base, quote, id }">
            <p style="margin: 0">{{ id }}</p>
            <h6>{{ base }}/{{ quote }}</h6>
          </template>
        </v-select>
      </b-nav-item>

      <b-nav-item style="margin-bottom:0.5rem; padding: 0.2rem 0 0 0.5rem; color: #568bff" target="_blank" :href="`https://pools.balancer.exchange/#/pool/${this.selected.id}`">
        Open in Balancer <feather-icon class="text-primary mr-1" icon="LinkIcon" />
      </b-nav-item>
      <b-form-radio-group
        :disabled="loading == true"
        id="btn-radios-1"
        v-model="timeframe"
        :options="['15min', '1H', '4H', '1D', '1W']"
        name="radios-btn-default"
        buttons
      ></b-form-radio-group>
      <b-nav-form>
        <b-form-checkbox :disabled="loading == true" style="margin-top: 0.318rem" v-model="baseSwitched" switch>Switch base</b-form-checkbox>
      </b-nav-form>
    </b-nav>

    <trading-vue
      :data="chart"
      :width="this.width"
      :height="this.height"
      ref="tvjs"
      :title-txt="this.selected.base ? this.selected.base + '/' + this.selected.quote : ''"
      :toolbar="true"
      :color-back="colors.colorBack"
      :color-grid="colors.colorGrid"
      :color-text="colors.colorText"
      :overlays="overlays"
      :legend-buttons="buttons"
      v-on:legend-button-click="saveIndicators"
      v-on:range-changed="rangeChanged"
      :extensions="ext"
    >
    </trading-vue>
  </div>
</template>

<script>
  import { BNav, BNavItem, BNavForm, BFormCheckbox, BFormRadioGroup } from 'bootstrap-vue'
  import ToastificationContent from '@core/components/toastification/ToastificationContent.vue'
  import { TradingVue, DataCube } from 'trading-vue-js'
  import XP from 'tvjs-xp'
  import Liquidity from '../overlays/Liquidity'
  import Overlays from 'tvjs-overlays'
  import vSelect from 'vue-select'
  export default {
    components: { TradingVue, BNav, BNavItem, BFormCheckbox, vSelect, BNavForm, ToastificationContent, BFormRadioGroup },
    data() {
      return {
        ext: Object.values(XP),
        chart: new DataCube({
          chart: {
            type: 'Candles',
            indexBased: false,
            data: [],
            settings: {
              showVolume: true
            }
          },
          onchart: this.$cookies.get('onchart') ? JSON.parse(this.$cookies.get('onchart')) : [],
          offchart: this.$cookies.get('offchart')
            ? JSON.parse(this.$cookies.get('offchart'))
            : [
                {
                  name: 'Liquidity',
                  type: 'Liquidity',
                  data: [],
                  settings: {
                    'z-index': 10
                  }
                }
              ]
        }),
        overlays: [Liquidity].concat(Object.values(Overlays)),
        width: window.innerWidth,
        height: window.innerHeight,
        night: true,
        selected: this.$route.query.pool
          ? { id: this.$route.query.pool }
          : !this.$cookies.get('pool')
          ? {
              id: '0x59a19d8c652fa0284f44113d0ff9aba70bd46fb4',
              liquidity: '263227428.3595805475021810313339604',
              base: 'BAL',
              quote: 'WETH',
              baseName: 'Balancer',
              quoteName: 'Wrapped Ether'
            }
          : this.$cookies.get('pool'),
        timeframe: this.$cookies.get('tf') ? this.$cookies.get('tf') : '1D',
        baseSwitched: this.$cookies.get('baseSwitched') ? this.$cookies.get('baseSwitched') : false,
        loading: false,
        firstTimestamp: undefined,
        pools: [],
        filteredOptions: [],
        inputProps: {
          id: 'autosuggest__input',
          // class: 'form-control',
          placeholder: 'BALANCER pool'
        },
        limit: 10,
        buttons: ['add', 'settings', 'up', 'down', 'remove']
      }
    },
    methods: {
      saveIndicators() {
        this.$cookies.set('offchart', JSON.stringify(this.chart.get('offchart')), Infinity)
        this.$cookies.set('onchart', JSON.stringify(this.chart.get('onchart')), Infinity)
      },
      selectFilter(option, label, search) {
        const temp = search.toLowerCase()
        return option.base.toLowerCase().indexOf(temp) > -1 || option.quote.toLowerCase().indexOf(temp) > -1 || option.id.toLowerCase().indexOf(temp) > -1
      },
      onInputChange(text) {
        if (text === '' || text === undefined) {
          return
        }
        /* Full control over filtering. Maybe fetch from API?! Up to you!!! */
        const filteredBases = this.pools.filter((item) => item.base.toLowerCase().indexOf(text.toLowerCase()) > -1).slice(0, this.limit)
        const filteredQuotes = this.pools.filter((item) => item.quote.toLowerCase().indexOf(text.toLowerCase()) > -1).slice(0, this.limit)
        const filteredIds = this.pools.filter((item) => item.id.toLowerCase().indexOf(text.toLowerCase()) > -1).slice(0, this.limit)
        const filteredBasesQuotes = filteredBases.concat(filteredQuotes.filter((item) => filteredBases.indexOf(item) < 0))
        const filteredData = filteredBasesQuotes.concat(filteredBasesQuotes.filter((item) => filteredIds.indexOf(item) < 0))
        this.filteredOptions = [
          {
            data: filteredData
          }
        ]
      },
      getSuggestionValue(object) {
        return `${object.item.base}-${object.item.quote}`
      },
      onResize(event) {
        this.width = window.innerWidth
        this.height = window.innerHeight - 38
      },
      async poolChanged(option) {
        if (option && option.id !== this.selected.id) {
          await this.loadData(true, option.id)
          this.$cookies.set('pool', this.selected, Infinity)
        }
      },
      async rangeChanged(ranges) {
        if (this.firstTimestamp > ranges[0]) {
          await this.loadData()
        }
      },
      async loadData(resetChart = false, poolId = this.selected.id) {
        if (poolId.length < 32) return
        if (this.loading == true) return
        this.loading = true
        if (resetChart) {
          this.firstTimestamp = undefined
          this.chart.set('chart.data', [])
          this.chart.set('offchart.Liquidity.data', [])
          this.chart.set('chart.tf', this.timeframe)
          this.$refs.tvjs.resetChart()
        }
        try {
          const chartData = await this.$http.get(
            `/chart/${poolId}?timeframe=${this.timeframe}${this.baseSwitched ? '&baseSwitch=1' : ''}${this.firstTimestamp ? `&before=${this.firstTimestamp}` : ''}`
          )

          if (chartData.data !== null) {
            if (typeof chartData.data === 'string') {
              this.$toast(
                {
                  component: ToastificationContent,
                  props: {
                    title: 'Notification',
                    icon: 'AlertTriangleIcon',
                    text: chartData.data,
                    variant: 'danger'
                  }
                },
                {
                  position: 'top-center'
                }
              )
            }

            this.firstTimestamp = chartData.data.bars[0][0]
            this.chart.merge('chart.data', chartData.data.bars)
            this.chart.merge('offchart.Liquidity.data', chartData.data.liquidity)
            this.selected = chartData.data.metadata
            this.$router.push({ path: '/', query: { pool: this.selected.id } }).catch((err) => {})
            // this.onResize()
            // this.$refs.tvjs.resetChart()
            this.$refs.tvjs.setRange(this.firstTimestamp, this.$refs.tvjs.getRange()[1])
            this.saveIndicators()
            this.rangeChanged(this.$refs.tvjs.getRange())
          }
        } catch (err) {
          console.log(err)
        }
        this.loading = false
      },
      async loadPoolsList() {
        const list = await this.$http.get('/pools')
        this.pools = list.data
      }
    },
    watch: {
      async baseSwitched(newValue, oldValue) {
        this.$cookies.set('baseSwitched', newValue, Infinity)
        await this.loadData(true)
      },
      async timeframe(newValue, oldValue) {
        this.$cookies.set('tf', newValue, Infinity)
        await this.loadData(true)
      }
    },
    computed: {
      colors() {
        return this.night
          ? {}
          : {
              colorBack: '#fff',
              colorGrid: '#eee',
              colorText: '#333'
            }
      }
    },
    async mounted() {
      window.addEventListener('resize', this.onResize)
      this.onResize()
      window.dc = this.chart
      window.tv = this.$refs.tvjs
      await this.loadPoolsList()
      await this.loadData()
    },
    beforeDestroy() {
      window.removeEventListener('resize', this.onResize)
    }
  }
</script>

<style lang="scss">
  @import '@core/scss/vue/libs/vue-select.scss';
</style>

<style>
  .btn-secondary {
    background-color: transparent !important;
    border-color: transparent !important;
  }

  .btn-secondary.active {
    background-color: transparent !important;
    border-color: transparent !important;
  }

  .btn-secondary.active span,
  .btn-secondary:focus span {
    color: #568bff !important;
  }
  .custom-control-input:checked ~ .custom-control-label::before {
    border-color: #568bff !important;
    background-color: #568bff !important;
  }

  .block {
    cursor: wait;
  }
</style>
